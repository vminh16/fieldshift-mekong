"""Candidate Generator, Feasibility, Response evaluation, Risk-aware Planner, Explanation, Twin.

Design v2 §6.4–6.8. The planner never produces a single "science score" for display: it keeps the
Pareto front and picks diverse strategies; farmer priorities only order the presentation.
"""

import datetime as dt
import itertools
import statistics as st
from functools import lru_cache
from time import perf_counter

from fieldshift.domain.catalog import CROP_BY_ID, CROPS
from fieldshift.domain.engines.future_outlook import (
    ENSO_SCENARIO_ID,
    PHASE_VI,
    analog_years,
    build_scenarios,
    build_weather,
    dry_season_rain,
    year_outlook,
)
from fieldshift.domain.engines.official_guidance import active_region
from fieldshift.domain.formatting import number_vi
from fieldshift.domain.value_objects.measure import measure

VERSIONS = {
    "catalog": CROPS["version"],
    "rules": "rules-1",
    "water_model": "fao56-v1",
    "planner": "pareto-v3-audit",
}
PPT_PER_DS_M = 0.64  # TDS ≈ 640·ECw (FAO-29, ECw < 5 dS/m); VN extension reports salinity in ‰
DEFAULT_CANAL_CAP_MM = (
    500.0  # ponytail: assumed per-season cap for "canal_limited"; ask farmer for real value
)
PRIORITY_TO_STRATEGY = {
    "save_water": "save_water",
    "avoid_crop_failure": "low_risk",
    "soil_health": "soil_support",
    "supplemental_income": "balanced",
    "minimal_change": "balanced",
}
STRATEGY_VI = {
    "save_water": "Tiết kiệm nước",
    "low_risk": "Giảm rủi ro",
    "soil_support": "Hỗ trợ đất",
    "balanced": "Thay đổi ít, cân bằng",
    "third_season_rest": "Nghỉ vụ ba / xả lũ",
    "salinity_avoidance": "Gieo đầu khung vụ",
}
# Strategies whose ranking prefers keeping the high-value seasons (production_value_index).
VALUE_AWARE_STRATEGIES = frozenset({"low_risk", "soil_support", "balanced"})
# 4 Pareto strategies + at most one zone practice (inland rest OR coastal early sow).
MAX_OPTIONS = 5
REST_WINDOW = "thu_dong"
EARLY_SOW_WINDOW = "dong_xuan"
VALUE_REASON_EVIDENCE = ["ev_value_heuristic", "ev_region_calendar"]
# criteria() reads climate/dry summaries; field_rules() reads climate only.
# Keep this set aligned with those dependencies so optional outlooks cannot change selection.
# When the ENSO analog scenario exists it is screened too and replaces sc_dry as the
# dry-year criterion (dry_scenario), so the shortlist can follow the year's ENSO state.
SCREENING_SCENARIOS = frozenset({"sc_clim", "sc_dry"})
HEAT_STRESS_DAYS_SOFT = 5
WATER_STRESS_DAYS_SOFT = 7
WATERLOG_RAIN_MM = 600
SALINITY_OVERLAP_DAYS = 7
SALINITY_EARLY_WEEKS = -4
# Horizons up to this many seasons are enumerated exhaustively; longer ones use a beam search
# keeping BEAM_WIDTH crop prefixes per season (design v2 §6.5.5: no global-optimum claim).
EXHAUSTIVE_MAX_SEASONS = 3
BEAM_WIDTH = 24
CONFIDENCE_HIGH_WIN_RATIO = 0.9
CONFIDENCE_MEDIUM_WIN_RATIO = 0.6
OUTLOOK_KINDS = ("FORECAST", "CLIMATE_PROJECTION")
ROBUSTNESS_RULE = (
    "Đạt tiêu chí nội bộ khi trung vị nước tưới mô hình thấp hơn hiện tại VÀ trung vị (ngày thiếu nước"
    " + ngày nắng nóng) không cao hơn hiện tại, trên cùng kịch bản; không phải kiểm định thực địa hay xác suất thành công."
)
CONFIDENCE_BASIS = (
    "Nhãn so sánh nội bộ, không phải xác suất thành công. HIGH: đạt ≥ 90 % kịch bản, không thiếu dữ liệu đầu vào của luật, trạng thái"
    " RECOMMEND_FOR_CONSIDERATION, không thua kịch bản dự báo mùa/CMIP6; MEDIUM: đạt ≥ 60 %;"
    " còn lại LOW. Chuỗi hiện tại là mốc so sánh nên chỉ xét dữ liệu thiếu và trạng thái."
)
SCENARIO_PRESENTATION = {
    "CLIMATOLOGY": ("inferred_by_model", "Dự kiến"),
    "FORECAST": ("forecast", "Dự báo mùa"),
    "CLIMATE_PROJECTION": ("climate_projection", "Khí hậu tương lai CMIP6"),
    "STRESS_TEST": ("assumed_scenario", "Kịch bản thử thách"),
}


# ---------- season windows & generator ----------


def _md(year: int, mmdd: str) -> dt.date:
    m, d = map(int, mmdd.split("-"))
    return dt.date(year, m, d)


def window_instances(region: dict, as_of: dt.date, n: int) -> list[dict]:
    out = []
    years_needed = (n + len(region["season_windows"]) - 1) // len(region["season_windows"])
    for y in range(as_of.year - 1, as_of.year + years_needed + 2):
        for w in region["season_windows"]:
            lo, hi = _md(y, w["sow_from"]), _md(y, w["sow_to"])
            if hi >= as_of:
                out.append(
                    {
                        "id": w["id"],
                        "name_vi": w["name_vi"],
                        "sow_from": max(lo, as_of),
                        "sow_to": hi,
                    }
                )
    return sorted(out, key=lambda w: w["sow_from"])[:n]


def sow_options(w: dict) -> list[tuple[str, dt.date]]:
    mid = w["sow_from"] + (w["sow_to"] - w["sow_from"]) / 2
    return (
        [("early", w["sow_from"]), ("standard", mid)]
        if mid != w["sow_from"]
        else [("standard", mid)]
    )


def make_sequence(windows, crops, sows) -> dict:
    seasons = []
    for i, (w, c, (tag, s)) in enumerate(zip(windows, crops, sows)):
        crop = CROP_BY_ID[c]
        seasons.append(
            {
                "index": i + 1,
                "window": w["id"],
                "window_name_vi": w["name_vi"],
                "crop": c,
                "crop_name_vi": crop["name_vi"],
                "sow_timing": tag,
                "sow": s,
                "harvest": s + dt.timedelta(days=crop["duration_days"]["typical"] - 1),
            }
        )
    return {
        "sequence_id": "seq_" + "_".join(crops) + "__" + "_".join(t for t, _ in sows),
        "crops": list(crops),
        "seasons": seasons,
    }


def calendar_rules(seq: dict, windows: list[dict], turnaround: int) -> list[dict]:
    rules = []
    for s, w in zip(seq["seasons"], windows):
        if w["id"] not in CROP_BY_ID[s["crop"]]["allowed_windows"]:
            rules.append(
                rule(
                    "R_WINDOW",
                    "HARD",
                    s["index"],
                    f"{s['crop_name_vi']} không thuộc lịch vụ {w['name_vi']} của vùng",
                    ["crops.allowed_windows", "regions.season_windows"],
                    "Chọn cây khác cho vụ này",
                    ["ev_crop_catalog", "ev_region_calendar"],
                )
            )
    for a, b in zip(seq["seasons"], seq["seasons"][1:]):
        if a["harvest"] + dt.timedelta(days=turnaround) > b["sow"]:
            rules.append(
                rule(
                    "R_SEASON_OVERLAP",
                    "HARD",
                    b["index"],
                    f"Thu hoạch {a['crop_name_vi']} ({a['harvest']}) + {number_vi(turnaround)} ngày làm đất vượt ngày gieo vụ {number_vi(b['index'])} ({b['sow']})",
                    ["crops.duration_days", "regions.min_turnaround_days"],
                    "Gieo vụ trước sớm hơn hoặc chọn giống ngắn ngày",
                    ["ev_crop_catalog", "ev_region_calendar"],
                )
            )
    return rules


def rule(rule_id, severity, season_index, reason, inputs_used, how_to_resolve, evidence):
    return {
        "rule_id": rule_id,
        "severity": severity,
        "season_index": season_index,
        "reason": reason,
        "inputs_used": inputs_used,
        "how_to_resolve": how_to_resolve,
        "evidence": evidence,
    }


# ---------- simulation ----------


def salinity_window(region: dict, as_of: dt.date, shift_weeks: int) -> tuple[dt.date, dt.date]:
    s = region["salinity_season"]
    for y in (as_of.year, as_of.year + 1):
        lo, hi = _md(y, s["typical_onset"]), _md(y, s["typical_end"])
        if hi >= as_of:
            return lo - dt.timedelta(
                days=(s.get("onset_advance_days", 0) if y == s.get("onset_advance_year", y) else 0)
            ) + dt.timedelta(weeks=shift_weeks), hi
    raise ValueError("no salinity window")


def overlap_days(a0, a1, b0, b1) -> int:
    return max(0, (min(a1, b1) - max(a0, b0)).days + 1)


@lru_cache(maxsize=8192)
def weekly_mean(values: tuple[float, ...], digits: int) -> float:
    # Repeated water-state patterns are common across crops/scenarios. Retain the
    # exact statistics.mean arithmetic (including rounding at half-way values).
    return round(st.mean(values), digits)


def weekly_water(rows: list[dict]) -> dict:
    return {
        "date": str(rows[0]["date"]),
        "stage": rows[0]["stage"],
        "root_depth_m": rows[0]["root_depth_m"],
        "root_zone_water": weekly_mean(tuple(x["water_frac"] for x in rows), 2),
        "ponding_mm": weekly_mean(tuple(x["ponding_mm"] for x in rows), 1)
        if rows[0]["ponding_mm"] is not None
        else None,
        "rain_week": round(sum(x["rain"] for x in rows), 1),
        "irrigation_week": sum(x["irrigation"] for x in rows),
        "ks": min(x["ks"] for x in rows),
        "stress_days": sum(x.get("stressed", 0) for x in rows),
    }


def week_stress_risk(crop: str | None, stress_days: int) -> str:
    """Weekly Twin flag on the engine's water_stress_days definition; bare fallow is never crop stress."""
    if not crop or CROP_BY_ID[crop]["water_regime"] == "none":
        return "LOW"
    return "HIGH" if stress_days >= 4 else "MEDIUM" if stress_days >= 1 else "LOW"


class Evaluator:
    """Simulates sequences across scenario members with memoisation (cache key = crop/sow/member/state)."""

    def __init__(
        self, ctx, state, field, as_of, span_days, irrigation_cap, override=None, *, simulate
    ):
        self.simulate = (
            simulate  # CropResponse port (FAO-56 adapter injected by the application layer)
        )
        self.ctx, self.state, self.field, self.as_of = ctx, state, field, as_of
        self.region = ctx["region"]
        self.lat, self.elev = (
            field["lat"],
            ctx["elevation_m"] if ctx["elevation_m"] is not None else ctx["grid_elevation_m"],
        )
        self.cap = irrigation_cap
        self.year_outlook = year_outlook(ctx, as_of, analog_years(ctx, as_of, span_days))
        self.region, self.salinity_adjusted = active_region(
            self.region, self.year_outlook, as_of, ctx["evidence"]
        )
        self.scenarios = build_scenarios(ctx, as_of, span_days, override, self.year_outlook)
        for scenario in self.scenarios:
            if self.salinity_adjusted:
                scenario["assumptions"].append(
                    "ASSUMPTION: SIWRR qua báo; khung mặn bắt đầu 01/12/2026 thay 15/01/2027"
                )
                scenario["evidence_ids"] = list(
                    dict.fromkeys([*scenario["evidence_ids"], "ev_siwrr_2026_press"])
                )
            if "ev_heat_conflict" in ctx["evidence"]:
                scenario["evidence_ids"] = list(
                    dict.fromkeys([*scenario["evidence_ids"], "ev_era5", "ev_heat_conflict"])
                )
        years = sorted(
            [
                m["year"]
                for s in self.scenarios
                if s["scenario_id"] == "sc_clim"
                for m in s["members"]
            ],
            key=lambda year: (dry_season_rain(ctx, as_of, year), year),
        )
        # Rank against all historical analogs: the wettest of the dry stress-test
        # subset must not be described as a wet year.
        self.year_labels = {}
        if len(years) >= 2:
            self.year_labels.update({years[0]: "Năm hạn", years[-1]: "Năm ướt"})
        if len(years) >= 3:
            self.year_labels[years[len(years) // 2]] = "Năm bình thường"
        self.weather = {}
        self.simulation_keys = {}
        weather_keys = {}
        for s in self.scenarios:
            for i, m in enumerate(s["members"]):
                key = (s["scenario_id"], i)
                # Climate, dry/wet analogs and salinity-only scenarios can share water
                # simulations. Forecast members retain distinct daily weather inputs.
                weather_key = (
                    m["year"],
                    m.get("temp_delta", 0.0),
                    m.get("rain_factor", 1.0),
                    tuple(sorted((m.get("monthly_tmax_delta") or {}).items())),
                    tuple(sorted((m.get("monthly_rain_factor") or {}).items())),
                    key if m.get("daily") else None,
                )
                canonical = weather_keys.setdefault(weather_key, key)
                self.simulation_keys[key] = canonical
                if canonical == key:
                    self.weather[key] = build_weather(
                        ctx,
                        as_of,
                        span_days,
                        m["year"],
                        m.get("temp_delta", 0.0),
                        m.get("rain_factor", 1.0),
                        m.get("monthly_tmax_delta"),
                        m.get("monthly_rain_factor"),
                        m.get("daily"),
                    )
                else:
                    self.weather[key] = self.weather[canonical]
        self.soil = {"taw_mm_per_m": self.region["soil_prior"]["taw_mm_per_m"]}
        self.memo = {}
        self.rain_memo = {}

    def weekly_rain(self, key, end):
        """Twin weekly rain per weather member; shared by every chain and alias scenario."""
        k = (self.simulation_keys[key], end)
        if k not in self.rain_memo:
            weather = {w["date"]: w for w in self.weather[key]}
            weeks = []
            for week in range((end - self.as_of).days // 7 + 1):
                date = self.as_of + dt.timedelta(days=week * 7)
                rain = sum(
                    weather.get(date + dt.timedelta(days=d), {}).get("rain_mm", 0) or 0
                    for d in range(min(7, (end - date).days + 1))
                )
                weeks.append(round(rain, 1))
            self.rain_memo[k] = weeks
        return self.rain_memo[k]

    def season(self, crop_id, sow, key, dep):
        if CROP_BY_ID[crop_id]["water_regime"] == "paddy":
            # Land preparation floods the paddy on day 0, so the incoming root-zone state does
            # not enter a paddy season; normalising it keeps one cached run per sow/member.
            dep = 0.0
        k = (crop_id, sow, self.simulation_keys[key], dep)
        if k not in self.memo:
            r = self.simulate(
                self.weather[key],
                CROP_BY_ID[crop_id],
                sow,
                self.lat,
                self.elev,
                self.region["paddy"],
                self.soil,
                dep,
                self.cap,
            )
            if CROP_BY_ID[crop_id]["water_regime"] == "none":
                # Bare-soil drying is not crop damage: a fallow season adds 0 stress days to
                # every total; the raw counts stay on the result for the Twin/debugging.
                for key in ("water_stress_days", "heat_stress_days_sensitive"):
                    r["bare_soil_" + key], r[key] = r[key], 0
            self.memo[k] = r
        return self.memo[k]

    def fallow_gap(self, start, next_sow, key, dep):
        """Advance [harvest + 1, next sow - 1] with the catalog's unirrigated cover bucket.

        This reuses the same fractional root-zone transfer as crop-to-crop carryover;
        it does not claim to track salt, nutrients or a common fixed soil depth.
        """
        days = (next_sow - start).days
        if days <= 0:
            return None
        k = ("gap", start, next_sow, self.simulation_keys[key], dep)
        if k not in self.memo:
            crop = {**CROP_BY_ID["fallow_cover"], "duration_days": {"typical": days}}
            self.memo[k] = self.simulate(
                self.weather[key],
                crop,
                start,
                self.lat,
                self.elev,
                self.region["paddy"],
                self.soil,
                dep,
                0.0,
            )
        return self.memo[k]

    def weekly(self, result):
        """Aggregate the original simulation only when a selected sequence needs Twin data."""
        if "weeks" not in result:
            daily = result.pop("daily")
            weeks = {}
            for row in daily:
                week = (row["date"] - self.as_of).days // 7
                weeks.setdefault(week, []).append(row)
            result["weeks"] = {week: weekly_water(rows) for week, rows in weeks.items()}
            result["season_weeks"] = [
                weekly_water(daily[i : i + 7]) for i in range(0, len(daily), 7)
            ]

    def run(self, seq, key):
        dep = self.state["initial_depletion_frac"]["value"]
        out = []
        previous = None
        for s in seq["seasons"]:
            if previous is not None:
                gap = self.fallow_gap(
                    previous["harvest"] + dt.timedelta(days=1), s["sow"], key, dep
                )
                if gap is not None:
                    dep = gap["end_state"]["depletion_frac"]
            r = self.season(s["crop"], s["sow"], key, dep)
            out.append(r)
            dep = r["end_state"]["depletion_frac"]  # inter-season water carry-over (AC-05)
            previous = s
        return out

    def evaluate(self, seq, scenario_ids=None) -> dict:
        res = {}
        for s in self.scenarios:
            if scenario_ids is not None and s["scenario_id"] not in scenario_ids:
                continue
            runs = [self.run(seq, (s["scenario_id"], i)) for i in range(len(s["members"]))]
            res[s["scenario_id"]] = runs
        return res


def q(vals, p):
    if len(vals) == 1:
        return vals[0]
    return st.quantiles(vals, n=10, method="inclusive")[p // 10 - 1] if p != 50 else st.median(vals)


def summarize(runs: list[list[dict]]) -> dict:
    def tot(r, k):
        return sum(x[k] for x in r)

    irr = [tot(r, "irrigation_mm") for r in runs]
    ws = [tot(r, "water_stress_days") for r in runs]
    hs = [tot(r, "heat_stress_days_sensitive") for r in runs]
    n = len(runs[0])
    return {
        "irrigation_mm": {"p50": round(q(irr, 50)), "p90": round(q(irr, 90))},
        "water_stress_days": {"p50": round(q(ws, 50), 1), "p90": round(q(ws, 90), 1)},
        "heat_stress_days_sensitive": {"p50": round(q(hs, 50), 1), "p90": round(q(hs, 90), 1)},
        "per_season": [
            {
                "irrigation_mm": round(st.median(r[i]["irrigation_mm"] for r in runs)),
                "water_stress_days": round(st.median(r[i]["water_stress_days"] for r in runs), 1),
                "heat_stress_days_sensitive": round(
                    st.median(r[i]["heat_stress_days_sensitive"] for r in runs), 1
                ),
                "rain_mm": round(st.median(r[i]["rain_mm"] for r in runs)),
                "etc_mm": round(st.median(r[i]["etc_mm"] for r in runs)),
            }
            for i in range(n)
        ],
        "members": len(runs),
    }


# ---------- feasibility needing outcomes / field state ----------


def field_rules(seq, ev: "Evaluator", summ: dict, constraints: dict) -> list[dict]:
    state, region = ev.state, ev.region
    rules = []
    coastal = state["coastal_salinity_risk"]["value"]
    anomaly = state.get("upstream_discharge_anomaly", {}).get("value")
    if coastal and anomaly is not None and anomaly < 0:
        rules.append(
            rule(
                "R_UPSTREAM_DISCHARGE_LOW",
                "SOFT",
                None,
                "Lưu lượng Mekong thượng nguồn thấp hơn nền cùng cửa sổ lịch; nên đo ECw nước kênh sớm hơn. Đây là tín hiệu vùng, không phải giá trị mặn.",
                ["state.upstream_discharge_anomaly"],
                "Đo ECw nước kênh sớm, đối chiếu bản tin địa phương",
                ["ev_glofas"],
            )
        )
    ecw = state["canal_ecw"]["value"]
    drainage = state["drainage"]["value"]
    sal_lo, sal_hi = salinity_window(region, ev.as_of, 0)
    early_lo, _ = salinity_window(region, ev.as_of, SALINITY_EARLY_WEEKS)
    for s, ps in zip(seq["seasons"], summ["sc_clim"]["per_season"]):
        c = CROP_BY_ID[s["crop"]]
        i = s["index"]
        if c["requires_good_drainage"]:
            if drainage == "poor":
                rules.append(
                    rule(
                        "R_DRAINAGE",
                        "HARD",
                        i,
                        f"{c['name_vi']} cần thoát nước tốt; nông dân báo ruộng thoát nước kém",
                        ["state.drainage", "crops.requires_good_drainage"],
                        "Lên liếp/đào rãnh thoát rồi cập nhật lại",
                        ["ev_crop_catalog"],
                    )
                )
            elif drainage in (None, "unknown"):
                rules.append(
                    rule(
                        "R_DRAINAGE_UNKNOWN",
                        "UNKNOWN_REQUIRES_CHECK",
                        i,
                        f"{c['name_vi']} cần thoát nước tốt; chưa xác nhận khả năng thoát nước",
                        ["state.drainage"],
                        "Kiểm tra ruộng còn đọng nước sau mưa lớn 24 h hay không",
                        ["ev_crop_catalog"],
                    )
                )
        if c["water_regime"] != "none" and coastal:
            ov = overlap_days(s["sow"], s["harvest"], sal_lo, sal_hi)
            ov_early = overlap_days(s["sow"], s["harvest"], early_lo, sal_hi)
            if ov_early >= SALINITY_OVERLAP_DAYS:
                thr = c["salinity"]["ecw_threshold_ds_m"]
                if ecw is None:
                    rules.append(
                        rule(
                            "R_SALINITY_UNKNOWN",
                            "UNKNOWN_REQUIRES_CHECK",
                            i,
                            f"Vụ {number_vi(i)} ({c['name_vi']}) trùng mùa mặn {number_vi(ov)} ngày ({number_vi(ov_early)} ngày nếu mặn đến sớm {number_vi(-SALINITY_EARLY_WEEKS)} tuần); chưa đo ECw nước kênh",
                            ["state.canal_ecw", "regions.salinity_season", "crops.salinity"],
                            f"Đo ECw nước kênh trước ngày gieo; ngưỡng tham khảo của {c['name_vi']} ≈ {number_vi(thr)} dS/m",
                            ["ev_salinity_season", "ev_crop_catalog"],
                        )
                    )
                elif ecw > thr:
                    ece = 1.5 * ecw
                    loss = max(
                        0.0,
                        c["salinity"]["slope_pct_per_ds_m"]
                        * (ece - c["salinity"]["ece_threshold_ds_m"]),
                    )
                    rules.append(
                        rule(
                            "R_SALINITY",
                            "SOFT",
                            i,
                            f"ECw đo được {number_vi(ecw)} dS/m > ngưỡng {number_vi(thr)} dS/m của {c['name_vi']}; giảm năng suất tham khảo ~{number_vi(min(100, round(loss)))}% (Maas-Hoffman, ECe≈1,5·ECw)",
                            ["state.canal_ecw", "crops.salinity"],
                            "Trữ nước ngọt, chọn cây/giống chịu mặn hơn hoặc dời lịch",
                            ["ev_crop_catalog"],
                        )
                    )
        if c["water_regime"] == "none":
            continue
        if ps["heat_stress_days_sensitive"] >= HEAT_STRESS_DAYS_SOFT:
            rules.append(
                rule(
                    "R_HEAT",
                    "SOFT",
                    i,
                    f"{c['name_vi']}: ước tính trung vị {number_vi(ps['heat_stress_days_sensitive'])} ngày Tmax ≥ {number_vi(c['heat']['tmax_threshold_c'])} °C ở giai đoạn nhạy cảm",
                    ["POWER/ERA5 heat_tmax (monthly conflict correction)", "crops.heat"],
                    "Dời ngày gieo để giai đoạn nhạy cảm tránh tháng nóng",
                    ["ev_power_daily", "ev_crop_catalog"]
                    + (
                        ["ev_era5", "ev_heat_conflict"]
                        if "ev_heat_conflict" in ev.ctx["evidence"]
                        else []
                    ),
                )
            )
        if ps["water_stress_days"] >= WATER_STRESS_DAYS_SOFT:
            rules.append(
                rule(
                    "R_WATER_STRESS",
                    "SOFT",
                    i,
                    f"{c['name_vi']}: trung vị {number_vi(ps['water_stress_days'])} ngày thiếu nước với nguồn tưới đã khai báo",
                    ["NASA POWER", "constraints.irrigation"],
                    "Tăng nguồn tưới hoặc chọn cây ít nước hơn",
                    ["ev_power_daily", "ev_crop_catalog"],
                )
            )
        if (
            c["water_regime"] == "upland"
            and c["waterlogging_tolerance"] == "low"
            and ps["rain_mm"] >= WATERLOG_RAIN_MM
        ):
            rules.append(
                rule(
                    "R_WATERLOG",
                    "SOFT",
                    i,
                    f"{c['name_vi']} chịu úng kém; mưa trung vị trong vụ {number_vi(ps['rain_mm'])} mm",
                    ["NASA POWER PRECTOTCORR", "crops.waterlogging_tolerance"],
                    "Lên liếp, rãnh thoát; tránh gieo đầu mùa mưa",
                    ["ev_power_daily"],
                )
            )
        if constraints.get("no_new_machinery") and c["machinery_required"]:
            rules.append(
                rule(
                    "R_MACHINERY",
                    "HARD",
                    i,
                    f"{c['name_vi']} cần {', '.join(c['machinery_required'])}; hộ không đầu tư máy mới",
                    ["constraints.no_new_machinery", "crops.machinery_required"],
                    "Thuê dịch vụ máy hoặc chọn cây khác",
                    ["ev_crop_catalog"],
                )
            )
        if constraints.get("budget_level") == "low" and c["relative_cost_level"] == "high":
            rules.append(
                rule(
                    "R_BUDGET",
                    "SOFT",
                    i,
                    f"{c['name_vi']} chi phí đầu tư tương đối cao so với ngân sách thấp",
                    ["constraints.budget_level", "crops.relative_cost_level"],
                    "Xác nhận vốn/tín dụng trước khi gieo",
                    ["ev_crop_catalog"],
                )
            )
    if all(c == "rice" for c in seq["crops"]):
        rules.append(
            rule(
                "R_PEST_CYCLE",
                "SOFT",
                None,
                "Lúa liên tục các vụ không cắt vòng đời sâu bệnh (ví dụ rầy nâu) — lợi ích luân canh tiềm năng, định tính",
                ["crops.soil_support_indicators"],
                "Cân nhắc 1 vụ màu hoặc nghỉ đất",
                ["ev_crop_catalog"],
            )
        )
    return rules


def status_of(rules) -> str:
    sev = {r["severity"] for r in rules}
    if "HARD" in sev:
        return "NOT_FEASIBLE"
    if "UNKNOWN_REQUIRES_CHECK" in sev:
        return "CONDITIONAL_PENDING_CHECK"
    return "RECOMMEND_FOR_CONSIDERATION"


def soil_indicators(seq) -> list[str]:
    ind = sorted({i for c in seq["crops"] for i in CROP_BY_ID[c]["soil_support_indicators"]})
    if len(set(seq["crops"])) > 1:
        ind.append(f"crop_diversity_{len(set(seq['crops']))}")
    return ind


# ---------- planner ----------


def production_value_index(seq: dict, region: dict) -> float:
    """Σ over seasons of season_value_weight(window) × value_index(crop).

    Team heuristic [B] (regions.json season_value_weight, crops.json value_index): an ordering
    aid so the planner does not trade away the most valuable season; not yield, price or profit.
    """
    weight = {w["id"]: w["value_weight"] for w in region["season_windows"]}
    return round(
        sum(weight[s["window"]] * CROP_BY_ID[s["crop"]]["value_index"] for s in seq["seasons"]), 2
    )


def salinity_exposure_days(seq: dict, region: dict, as_of: dt.date, shift_weeks: int) -> int:
    """Days crop seasons (not fallow) overlap the salinity window, same dates as field_rules."""
    lo, hi = salinity_window(region, as_of, shift_weeks)
    return sum(
        overlap_days(s["sow"], s["harvest"], lo, hi)
        for s in seq["seasons"]
        if CROP_BY_ID[s["crop"]]["water_regime"] != "none"
    )


def dry_scenario(summary: dict) -> str:
    """Scenario id behind the dry-year criterion: ENSO analog years when available."""
    return ENSO_SCENARIO_ID if ENSO_SCENARIO_ID in summary else "sc_dry"


def criteria(c, baseline):
    s = c["summary"]
    return {
        "value": -c["production_value_index"],  # maximised; negated for the min-Pareto
        "irr": s["sc_clim"]["irrigation_mm"]["p50"],
        "irr_dry": s[dry_scenario(s)]["irrigation_mm"]["p50"],
        "stress_p90": s["sc_clim"]["water_stress_days"]["p90"]
        + s["sc_clim"]["heat_stress_days_sensitive"]["p90"],
        "salt": sum(1 for r in c["rules"] if r["rule_id"].startswith("R_SALINITY")),
        "soil": -len(c["soil_indicators"]),
        "changes": sum(1 for a, b in zip(c["seq"]["crops"], baseline["seq"]["crops"]) if a != b),
        "idle": c["seq"]["crops"].count("fallow_cover"),
    }


PARETO_KEYS = ("irr", "irr_dry", "stress_p90", "salt", "soil", "changes", "idle", "value")


def pareto(cands):
    """Non-dominated candidates, in input order.

    A dominator is lexicographically smaller, so after sorting each candidate only needs
    checking against the front found so far (dominance is transitive): O(n·|front|).
    """
    vecs = {id(c): tuple(c["crit"][k] for k in PARETO_KEYS) for c in cands}
    front = []
    for a in sorted(cands, key=lambda c: vecs[id(c)]):
        va = vecs[id(a)]
        if not any(f != va and all(x <= y for x, y in zip(f, va)) for f in front):
            front.append(va)
    front = set(front)
    return [c for c in cands if vecs[id(c)] in front]


def stress_p50(s):
    return round(s["water_stress_days"]["p50"] + s["heat_stress_days_sensitive"]["p50"], 1)


def robustness(c, base) -> dict:
    """Wins vs the baseline on the same scenario ids; the rule is ROBUSTNESS_RULE."""
    lost = [
        sid
        for sid, s in c["summary"].items()
        if not (
            s["irrigation_mm"]["p50"] < base["summary"][sid]["irrigation_mm"]["p50"]
            and stress_p50(s) <= stress_p50(base["summary"][sid])
        )
    ]
    total = len(c["summary"])
    return {
        "wins": total - len(lost),
        "total": total,
        "lost_scenarios": lost,
        "rule": ROBUSTNESS_RULE,
    }


def confidence(c, robust, state, scen) -> dict:
    """Transparent level; robust is None for the baseline (the reference itself)."""
    unknowns = sorted(
        {
            var
            for r in c["rules"]
            for inp in r["inputs_used"]
            if inp.startswith("state.")
            and (var := inp.removeprefix("state.")) in state
            and state[var]["value"] in (None, "unknown")
        }
    )
    ratio = 1.0 if robust is None else robust["wins"] / robust["total"]
    lost_outlook = robust is not None and any(
        scen[sid]["kind"] in OUTLOOK_KINDS for sid in robust["lost_scenarios"]
    )
    if (
        ratio >= CONFIDENCE_HIGH_WIN_RATIO
        and not unknowns
        and c["status"] == "RECOMMEND_FOR_CONSIDERATION"
        and not lost_outlook
    ):
        level = "HIGH"
    elif ratio >= CONFIDENCE_MEDIUM_WIN_RATIO:
        level = "MEDIUM"
    else:
        level = "LOW"
    return {
        "level": level,
        "robust_scenarios": "n/a" if robust is None else f"{robust['wins']}/{robust['total']}",
        "unknowns": unknowns,
        "basis": CONFIDENCE_BASIS,
    }


def strategy_order(priorities):
    order = []
    for priority in priorities:
        strategy = PRIORITY_TO_STRATEGY.get(priority)
        if strategy and strategy not in order:
            order.append(strategy)
    return order + [s for s in STRATEGY_VI if s not in order]


def rerank_options(options, priorities):
    """Fixed diverse shortlist is priority-independent; priorities only reorder it (§6.7)."""
    order = strategy_order(priorities)
    return sorted(options, key=lambda option: order.index(option["strategy_tag"]))


def rests_third_season(c, baseline) -> bool:
    """Baseline with only its Thu Đông crop(s) replaced by fallow, same sow timings."""
    pairs = list(zip(c["seq"]["seasons"], baseline["seq"]["seasons"]))
    changed = [s for s, b in pairs if s["crop"] != b["crop"]]
    return (
        bool(changed)
        and all(s["window"] == REST_WINDOW and s["crop"] == "fallow_cover" for s in changed)
        and all(s["sow_timing"] == b["sow_timing"] for s, b in pairs)
    )


def sows_dong_xuan_early(c, baseline) -> bool:
    """Baseline crops, Đông Xuân sown early, every other season at the baseline timing."""
    pairs = list(zip(c["seq"]["seasons"], baseline["seq"]["seasons"]))
    return (
        c["seq"]["crops"] == baseline["seq"]["crops"]
        and any(s["window"] == EARLY_SOW_WINDOW and s["sow"] < b["sow"] for s, b in pairs)
        and all(
            s["sow_timing"] == ("early" if s["window"] == EARLY_SOW_WINDOW else b["sow_timing"])
            for s, b in pairs
        )
    )


def salinity_avoided(c, baseline) -> dict:
    """Salinity-window overlap days removed vs the baseline (typical and early-onset windows)."""
    return {k: baseline["salinity_exposure"][k] - v for k, v in c["salinity_exposure"].items()}


def pick_strategies(front, baseline, priorities, evaluated=(), coastal=False):
    """Diverse Pareto picks, plus one named zone practice chosen from all feasible candidates.

    The practices (inland third-season rest, coastal early Đông Xuân sowing) are defined by
    agronomic practice, not by the Pareto keys, whose criteria cannot see their benefits.
    """
    picked, used = [], set()
    practice, test = (
        ("salinity_avoidance", sows_dong_xuan_early)
        if coastal
        else ("third_season_rest", rests_third_season)
    )
    c = next((c for c in evaluated if test(c, baseline)), None)
    if c is not None and (not coastal or salinity_avoided(c, baseline)["typical"] > 0):
        used.add(tuple(c["seq"]["crops"]))
        picked.append((practice, c))
    pool = [c for c in front if c["seq"]["crops"] != baseline["seq"]["crops"]]
    by = {
        "save_water": lambda c: (c["crit"]["idle"], c["crit"]["irr"], c["crit"]["irr_dry"]),
        "low_risk": lambda c: (
            c["crit"]["salt"],
            c["crit"]["idle"],
            c["crit"]["value"],
            c["crit"]["stress_p90"],
            c["crit"]["irr_dry"],
        ),
        "soil_support": lambda c: (c["crit"]["soil"], c["crit"]["value"], c["crit"]["irr"]),
        "balanced": lambda c: (
            c["crit"]["changes"],
            c["crit"]["value"],
            c["crit"]["stress_p90"],
            c["crit"]["irr"],
        ),
    }
    order = strategy_order(priorities)
    for s in by:  # assign in fixed order so labels don't depend on priorities; priorities only reorder (§6.7.4)
        for c in sorted(pool, key=by[s]):
            sig = tuple(c["seq"]["crops"])
            if sig not in used:  # no near-duplicates (same crops, different sow date)
                used.add(sig)
                picked.append((s, c))
                break
    return sorted(picked, key=lambda x: order.index(x[0]))[:MAX_OPTIONS]


# ---------- explanation ----------


def strategy_reasons(c, base, ev, strategy) -> tuple[list[dict], dict | None]:
    """(leading practice/value reasons, value trade-off reason to place after the first one)."""
    lead = []
    if strategy == "third_season_rest":
        lead.append(
            {
                "text": "Nghỉ vụ ba (Thu Đông) — lợi ích tiềm năng, định tính, chưa định lượng: cắt vòng đời rầy nâu vì ruộng không có lúa, đất được nghỉ, và nhận phù sa nếu ruộng nằm trong vùng xả lũ đầu nguồn.",
                "claim_type": "POTENTIAL_QUALITATIVE",
                "evidence_ids": ["ev_crop_catalog", "ev_region_calendar"],
            }
        )
    if strategy == "salinity_avoidance":
        avoided = salinity_avoided(c, base)
        lo, hi = salinity_window(ev.region, ev.as_of, 0)
        early = next(s for s in c["seq"]["seasons"] if s["window"] == EARLY_SOW_WINDOW)
        lead.append(
            {
                "text": f"Giữ chuỗi cây hiện tại, gieo đầu khung vụ {early['window_name_vi']} ({early['sow']}, thu hoạch {early['harvest']}): bớt {number_vi(avoided['typical'])} ngày trùng khung mặn đang dùng ({lo}–{hi}) và {number_vi(avoided['early_onset'])} ngày nếu mặn đến sớm {number_vi(-SALINITY_EARLY_WEEKS)} tuần, so với gieo chuẩn. Không loại bỏ rủi ro mặn: vẫn phải đo ECw nước kênh trước khi gieo.",
                "evidence_ids": ["ev_salinity_season", "ev_region_calendar"]
                + (["ev_official_2504"] if "ev_official_2504" in ev.ctx["evidence"] else []),
            }
        )
    vc, vb = c["production_value_index"], base["production_value_index"]
    if vc == vb:
        return lead, None
    weight = {w["id"]: w["value_weight"] for w in ev.region["season_windows"]}
    top = max(weight, key=weight.get)
    changed = [
        s for s, b in zip(c["seq"]["seasons"], base["seq"]["seasons"]) if s["crop"] != b["crop"]
    ]
    detail = "đổi vụ " + ", ".join(s["window_name_vi"] for s in changed)
    kept = next((s for s in c["seq"]["seasons"] if s["window"] == top), None)
    if kept and all(s["window"] != top for s in changed):
        detail = f"giữ {kept['crop_name_vi'].lower()} vụ {kept['window_name_vi']} (vụ được nhóm ưu tiên giữ), chỉ {detail}"
    value = {
        "text": f"Điểm tham khảo do nhóm tự đặt là {number_vi(vc)} so với {number_vi(vb)} hiện tại: {detail}; chỉ giúp so sánh cách giữ vụ, không phải năng suất hay lợi nhuận.",
        "evidence_ids": VALUE_REASON_EVIDENCE,
    }
    return lead, value


def explain(c, base, ev, strategy=None) -> dict:
    s, b = c["summary"]["sc_clim"], base["summary"]["sc_clim"]
    sd, bd = c["summary"]["sc_dry"], base["summary"]["sc_dry"]
    reasons = []
    d = s["irrigation_mm"]["p50"] - b["irrigation_mm"]["p50"]
    if d <= -50:
        reasons.append(
            {
                "text": f"Ước tính mô hình: nhu cầu tưới trung vị giảm ~{number_vi(-d)} mm (~{number_vi(-d * 10)} m³/ha) so với hiện tại trên cùng {number_vi(s['members'])} năm lịch sử NASA POWER.",
                "evidence_ids": ["ev_power_daily", "ev_crop_catalog"],
            }
        )
    dd = sd["irrigation_mm"]["p50"] - bd["irrigation_mm"]["p50"]
    outlook = ev.year_outlook
    de = 0
    if outlook["status"] == "OK":
        se, be = c["summary"][ENSO_SCENARIO_ID], base["summary"][ENSO_SCENARIO_ID]
        de = se["irrigation_mm"]["p50"] - be["irrigation_mm"]["p50"]
        if de <= -50:  # the analog scenario is the dry-year criterion this year: say so first
            reasons.insert(
                0,
                {
                    "text": f"Trong các năm tương tự ENSO hiện tại ({PHASE_VI[outlook['enso']['phase']]}: {', '.join(outlook['analog_labels_vi'])}), mô hình ước tính giảm ~{number_vi(-de)} mm nước tưới so với hiện tại (năm tương tự, không phải dự báo).",
                    "evidence_ids": list(outlook["evidence_ids"]),
                },
            )
    if dd <= -50 and de > -50:
        reasons.append(
            {
                "text": f"Trong các năm khô nhất, mô hình ước tính giảm ~{number_vi(-dd)} mm nước tưới so với hiện tại.",
                "evidence_ids": ["ev_power_daily"],
            }
        )
    water_stress_delta = s["water_stress_days"]["p50"] - b["water_stress_days"]["p50"]
    if water_stress_delta < 0:
        reasons.append(
            {
                "text": f"Mô hình ước tính bớt {number_vi(-water_stress_delta)} ngày thiếu nước so với hiện tại.",
                "evidence_ids": ["ev_power_daily", "ev_crop_catalog"],
            }
        )
    if "R_PEST_CYCLE" in {r["rule_id"] for r in base["rules"]} and "R_PEST_CYCLE" not in {
        r["rule_id"] for r in c["rules"]
    }:
        reasons.append(
            {
                "text": "Luân phiên cây hoặc nghỉ vụ có thể cắt vòng sâu bệnh của lúa liên tục; lợi ích định tính, chưa mô phỏng sâu bệnh.",
                "evidence_ids": ["ev_crop_catalog"],
            }
        )
    ds = s["heat_stress_days_sensitive"]["p50"] - b["heat_stress_days_sensitive"]["p50"]
    if ds <= -3:
        reasons.append(
            {
                "text": f"Ước tính bớt ~{number_vi(-ds)} ngày nắng nóng (≥ ngưỡng cây) ở giai đoạn nhạy cảm; dùng quy tắc đối chiếu POWER–ERA5 nếu có.",
                "evidence_ids": ["ev_power_daily", "ev_crop_catalog"]
                + (
                    ["ev_era5", "ev_heat_conflict"]
                    if "ev_heat_conflict" in ev.ctx["evidence"]
                    else []
                ),
            }
        )
    sal_b = sum(1 for r in base["rules"] if r["rule_id"].startswith("R_SALINITY"))
    sal_c = sum(1 for r in c["rules"] if r["rule_id"].startswith("R_SALINITY"))
    if sal_c < sal_b:
        reasons.append(
            {
                "text": "Ít vụ trùng mùa mặn hơn chuỗi hiện tại.",
                "evidence_ids": ["ev_salinity_season"],
            }
        )
    added = [i for i in c["soil_indicators"] if i not in base["soil_indicators"]]
    if added:
        reasons.append(
            {
                "text": "Lợi ích tiềm năng cho đất (định tính): " + ", ".join(added),
                "evidence_ids": ["ev_crop_catalog"],
            }
        )
    lead, value = strategy_reasons(c, base, ev, strategy)
    reasons += lead
    if ev.state["coastal_salinity_risk"]["value"]:
        lo, hi = salinity_window(ev.region, ev.as_of, 0)
        refs = ["ev_salinity_season"] + (["ev_siwrr_2026_press"] if ev.salinity_adjusted else [])
        reasons.insert(
            0,
            {
                "text": f"Cây đứng trong khung mặn {number_vi(c['salinity_exposure']['typical'])} ngày thay vì {number_vi(base['salinity_exposure']['typical'])} ngày của hiện tại ({lo}–{hi}); đây là số ngày phơi nhiễm theo lịch, chưa đo mặn tại thửa. Vẫn phải đo ECw và xác nhận nguồn nước ngọt.",
                "evidence_ids": refs,
            },
        )
    if "ev_official_2504" in ev.ctx["evidence"] and ev.as_of.year == 2026:
        changed = [
            (x, y)
            for x, y in zip(c["seq"]["seasons"], base["seq"]["seasons"])
            if x["crop"] != y["crop"] and y["crop"] == "rice"
        ]
        if changed:
            direction = (
                "giảm từ 3 vụ lúa xuống 2 vụ"
                if any(x["crop"] == "fallow_cover" for x, _ in changed)
                and len(c["seq"]["seasons"]) == 3
                and base["seq"]["crops"].count("rice") == 3
                else "chuyển một phần đất lúa sang cây cạn dùng ít nước"
            )
            reasons.append(
                {
                    "text": f"Cùng hướng Công văn 2504/TTTV-TTBVTV (19/6/2026): {direction} ở nơi thiếu nước hoặc 3 vụ kém hiệu quả. Cần xác nhận điều kiện cấp nước và thoát nước tại thửa.",
                    "evidence_ids": ["ev_official_2504"],
                }
            )
        for season in c["seq"]["seasons"]:
            if season["window"] == EARLY_SOW_WINDOW:
                sow = season["sow"]
                label = (
                    "đợt 1 (01–30/11/2026)"
                    if dt.date(2026, 11, 1) <= sow <= dt.date(2026, 11, 30)
                    else "đợt 2 (01–31/12/2026)"
                    if dt.date(2026, 12, 1) <= sow <= dt.date(2026, 12, 31)
                    else "ngoài hai đợt tháng 11–12; cần xác minh lịch địa phương"
                )
                reasons.append(
                    {
                        "text": f"Ngày gieo {sow} thuộc {label}. Khung gieo sớm né mặn chính thức 10–30/10/2026 {'đã qua' if ev.as_of > dt.date(2026, 10, 30) else 'cần đối chiếu theo ngày lập kế hoạch'}; gieo đầu khung của engine không đồng nghĩa gieo sớm né mặn.",
                        "evidence_ids": ["ev_official_2504", "ev_region_calendar"],
                    }
                )
                break
    if value:
        reasons.append(value)
    if not reasons:
        reasons.append(
            {
                "text": "Không khác biệt lớn so với hiện tại về nước/stress trong dữ liệu lịch sử.",
                "evidence_ids": ["ev_power_daily"],
            }
        )

    triggers, checklist = [], []
    for r in c["rules"]:
        if r["rule_id"] == "R_SALINITY_UNKNOWN":
            crop = CROP_BY_ID[c["seq"]["seasons"][r["season_index"] - 1]["crop"]]
            season = c["seq"]["seasons"][r["season_index"] - 1]
            thr = crop["salinity"]["ecw_threshold_ds_m"]
            triggers.append(
                {
                    "condition": f"ECw nước kênh > {number_vi(thr)} dS/m (≈ {number_vi(thr * PPT_PER_DS_M, 1)} ‰) trước {season['sow']}",
                    "measure": "ECw nước kênh (máy đo EC cầm tay)",
                    "variable": "canal_ecw",
                    "op": "gt",
                    "threshold": thr,
                    "season_index": r["season_index"],
                    "unit": "dS/m",
                    "action": f"Không gieo {crop['name_vi']} vụ {number_vi(r['season_index'])}; tái lập kế hoạch",
                }
            )
        if r["severity"] == "UNKNOWN_REQUIRES_CHECK":
            checklist.append(r["how_to_resolve"])
    for season in c["seq"]["seasons"]:
        crop = CROP_BY_ID[season["crop"]]
        if crop["requires_good_drainage"]:
            triggers.append(
                {
                    "condition": f"Thoát nước kém trước vụ {number_vi(season['index'])}",
                    "variable": "drainage",
                    "op": "eq",
                    "threshold": "poor",
                    "unit": None,
                    "season_index": season["index"],
                    "measure": "Khả năng thoát nước tại ruộng",
                    "action": "Xác nhận thoát nước và tái lập kế hoạch",
                }
            )
        if (
            ev.state["coastal_salinity_risk"]["value"]
            and crop["water_regime"] != "none"
            and not any(
                t.get("variable") == "canal_ecw" and t.get("season_index") == season["index"]
                for t in triggers
            )
        ):
            threshold = crop["salinity"]["ecw_threshold_ds_m"]
            triggers.append(
                {
                    "condition": f"ECw nước kênh > {number_vi(threshold)} dS/m trước {season['sow']}",
                    "variable": "canal_ecw",
                    "op": "gt",
                    "threshold": threshold,
                    "unit": "dS/m",
                    "season_index": season["index"],
                    "measure": "ECw nước kênh (máy đo EC cầm tay)",
                    "action": "Đo ECw, xác minh nguồn nước và tái lập kế hoạch",
                }
            )
    for crop in {
        c2 for c2 in c["seq"]["crops"] if c2 not in base["seq"]["crops"] and c2 != "fallow_cover"
    }:
        checklist.append(
            f"Xác nhận nguồn giống và đầu ra cho {CROP_BY_ID[crop]['name_vi']} ({CROP_BY_ID[crop]['market_note_vi']})"
        )
    checklist.append("Trao đổi với cán bộ khuyến nông địa phương trước khi xuống giống")
    risks = [
        {
            "code": r["rule_id"],
            "severity": r["severity"],
            "season_index": r["season_index"],
            "text": r["reason"],
        }
        for r in c["rules"]
        if r["severity"] in ("SOFT", "UNKNOWN_REQUIRES_CHECK")
    ]
    return {
        "reasons": reasons,
        "risks": risks,
        "triggers": triggers,
        "checklist": list(dict.fromkeys(checklist)),
    }


def metrics_view(summary: dict, base_summary: dict | None, scen: dict) -> tuple[dict, dict]:
    metrics, delta = {}, {}
    for sid, s in summary.items():
        origin, label = SCENARIO_PRESENTATION[scen[sid]["kind"]]

        evidence_ids = list(
            dict.fromkeys([*scen[sid]["evidence_ids"], "ev_power_daily", "ev_crop_catalog"])
        )

        def m(v, u):
            return measure(v, u, origin, label, evidence_ids)

        metrics[sid] = {
            "irrigation_need": m(s["irrigation_mm"]["p50"], "mm"),
            "irrigation_need_bad_year": m(s["irrigation_mm"]["p90"], "mm"),
            "water_stress_days": m(s["water_stress_days"]["p50"], "day"),
            "heat_stress_days_sensitive_stage": m(s["heat_stress_days_sensitive"]["p50"], "day"),
            "yield": measure(
                None, "t/ha", "unknown", "Chưa biết", reason="MODEL_NOT_CALIBRATED_G7"
            ),
            "profit": measure(None, "VND/ha", "unknown", "Chưa biết", reason="NO_PRICE_COST_DATA"),
            "per_season": s["per_season"],
            "years_used": s["members"],
        }
        if base_summary:
            b = base_summary[sid]
            delta[sid] = {
                "irrigation_need": {
                    "value": s["irrigation_mm"]["p50"] - b["irrigation_mm"]["p50"],
                    "unit": "mm",
                },
                "water_stress_days": {
                    "value": round(
                        s["water_stress_days"]["p50"] - b["water_stress_days"]["p50"], 1
                    ),
                    "unit": "day",
                },
                "heat_stress_days_sensitive_stage": {
                    "value": round(
                        s["heat_stress_days_sensitive"]["p50"]
                        - b["heat_stress_days_sensitive"]["p50"],
                        1,
                    ),
                    "unit": "day",
                },
            }
            for metric in delta[sid].values():
                metric.update(evidence_ids=evidence_ids, origin=origin, label=label)
    return metrics, delta


# ---------- twin ----------


def member_identity(scen: dict, i: int) -> dict:
    member = scen["members"][i]
    if scen["kind"] == "FORECAST":
        return {"member": i, "year": None, "member_label": f"SEAS5 member {member['member_id']}"}
    return {"member": i, "year": member["year"]}


def distribution_view(results: dict, scenarios: dict, summary: dict) -> dict:
    """Quantize to integer mm while retaining the existing rounded p50 exactly.

    Centering the rounding grid on p50 moves any member by at most 1 mm and
    avoids a half-mm median for an even ensemble. Stress counts are already ints.
    Use twentieths of a mm: season totals have tenth-mm precision, and their
    median may lie halfway between two tenths.
    """
    distributions = {}
    for sid, runs in results.items():
        tenths = [sum(round(r["irrigation_mm"] * 10) for r in run) for run in runs]
        offset = 20 * summary[sid]["irrigation_mm"]["p50"] - round(2 * st.median(tenths))
        distributions[sid] = [
            {
                **member_identity(scenarios[sid], i),
                "irrigation_mm": round((2 * tenths[i] + offset) / 20),
                "water_stress_days": sum(r["water_stress_days"] for r in run),
                "heat_stress_days": sum(r["heat_stress_days_sensitive"] for r in run),
            }
            for i, run in enumerate(runs)
        ]
    return distributions


def twin_events(ev: Evaluator, seq: dict, sal_shift: int, end: dt.date) -> list[dict]:
    events = [
        {"date": str(s[kind]), "type": kind, "season_index": s["index"], "crop": s["crop"]}
        for s in seq["seasons"]
        for kind in ("sow", "harvest")
    ]
    # Salinity boundaries describe the region, not a particular crop. Include each
    # season intersecting the shared horizon (also works for a multi-year plan).
    for year in range(ev.as_of.year - 1, end.year + 1):
        lo, hi = salinity_window(ev.region, dt.date(year, 1, 1), sal_shift)
        for kind, date in (("salinity_season_start", lo), ("salinity_season_end", hi)):
            if ev.as_of <= date <= end:
                events.append({"date": str(date), "type": kind, "season_index": None, "crop": None})
    return sorted(events, key=lambda event: (event["date"], event["type"]))


def trajectory_members(ev: Evaluator, c: dict, scen: dict, end: dt.date) -> dict:
    """Store compact weekly values; the application adds Measures on read."""
    sid = scen["scenario_id"]
    outcomes = c["distribution"][sid]
    # Preserve the original median-member selection using unquantized totals.
    totals = [
        sum(r["irrigation_mm"] for r in ev.run(c["seq"], (sid, i))) for i in range(len(outcomes))
    ]
    default = sorted(range(len(totals)), key=lambda i: (totals[i], i))[len(totals) // 2]
    members = []
    for i, outcome in enumerate(outcomes):
        label = ev.year_labels.get(outcome["year"], "Năm tham chiếu")
        if outcome["year"] is None:
            label = outcome["member_label"]
        elif label in ("Năm hạn", "Năm ướt"):
            label += f" như {outcome['year']}–{outcome['year'] + 1}"
        members.append(
            {
                **member_identity(scen, i),
                "irrigation_mm": outcome["irrigation_mm"],
                "label_vi": label,
            }
        )
    series_by_member, compare_series_by_member = [], []
    for i in range(len(members)):
        seasons = ev.run(c["seq"], (sid, i))
        for result in seasons:
            ev.weekly(result)
        rain_weeks = ev.weekly_rain((sid, i), end)
        series, cum = [], 0.0
        for week in range((end - ev.as_of).days // 7 + 1):
            date = ev.as_of + dt.timedelta(days=week * 7)
            active = [
                (s, r["weeks"][week])
                for s, r in zip(c["seq"]["seasons"], seasons)
                if week in r["weeks"]
            ]
            # Turnaround rules normally keep crops in separate weeks. If a week
            # contains a harvest and a new sow, draw the later crop; count all water.
            season, water = active[-1] if active else (None, {})
            irrigation = sum(row["irrigation_week"] for _, row in active)
            cum += irrigation
            stress_days = sum(
                row["stress_days"]
                for sn, row in active
                if CROP_BY_ID[sn["crop"]]["water_regime"] != "none"
            )
            series.append(
                {
                    "date": str(date),
                    "season_index": season["index"] if season else None,
                    "crop": season["crop"] if season else None,
                    "stage": water.get("stage"),
                    "root_depth_m": water.get("root_depth_m"),
                    "root_zone_water": water.get("root_zone_water"),
                    "ponding_mm": water.get("ponding_mm"),
                    "rain_week": rain_weeks[week],
                    "irrigation_week": round(irrigation, 1),
                    "irrigation_cum": round(cum),
                    "stress_risk": week_stress_risk(
                        season["crop"] if season else None, stress_days
                    ),
                }
            )
        compare_series_by_member.append(series)
        native = []
        for season, result in zip(c["seq"]["seasons"], seasons):
            cum = 0.0
            for week in result["season_weeks"]:
                cum += week["irrigation_week"]
                native.append(
                    {
                        **{k: v for k, v in week.items() if k not in ("ks", "stress_days")},
                        "season_index": season["index"],
                        "crop": season["crop"],
                        "irrigation_week": round(week["irrigation_week"], 1),
                        "irrigation_cum": round(cum),
                        "stress_risk": week_stress_risk(season["crop"], week["stress_days"]),
                    }
                )
        series_by_member.append(native)
    return {
        "default_member": default,
        "members": members,
        "events": twin_events(ev, c["seq"], scen["salinity_shift_weeks"], end),
        "series_by_member": series_by_member,
        "compare_series_by_member": compare_series_by_member,
        "salinity_windows": [
            [
                str(d)
                for d in salinity_window(
                    ev.region, dt.date(year, 1, 1), scen["salinity_shift_weeks"]
                )
            ]
            for year in range(ev.as_of.year - 1, end.year + 1)
        ],
        "coastal": bool(ev.state["coastal_salinity_risk"]["value"]),
        "canal_ecw": ev.state["canal_ecw"],
        "evidence_ids": list(
            dict.fromkeys([*scen["evidence_ids"], "ev_power_daily", "ev_crop_catalog"])
        ),
        "kind": scen["kind"],
    }


def trajectory(stored: dict, member: int | None = None, *, aligned: bool = False) -> dict:
    """Expand a persisted weekly slice. No weather loading or simulation here."""
    member = stored["default_member"] if member is None else member
    identity = stored["members"][member]
    coastal = stored["canal_ecw"]
    origin, label = SCENARIO_PRESENTATION[stored["kind"]]

    def m(value, unit, reason=None):
        return measure(value, unit, origin, label, stored["evidence_ids"], reason=reason)

    series = []
    series_key = "compare_series_by_member" if aligned else "series_by_member"
    for row in stored[series_key][member]:
        sal = measure(
            coastal["value"],
            "dS/m",
            coastal["origin"],
            coastal["label"],
            coastal.get("evidence_ids", []),
            reason="CANAL_ECW_NOT_MEASURED",
        )
        in_sal = any(lo <= row["date"] <= hi for lo, hi in stored["salinity_windows"])
        sal["in_salinity_season"] = stored["coastal"] and in_sal
        series.append(
            {
                **row,
                "root_zone_water": m(row["root_zone_water"], "fraction", "NO_ACTIVE_CROP"),
                "ponding_mm": m(
                    row["ponding_mm"], "mm", "NOT_PADDY" if row["crop"] else "NO_ACTIVE_CROP"
                ),
                "root_depth_m": m(row["root_depth_m"], "m", "NO_ACTIVE_CROP"),
                "rain_week": m(row["rain_week"], "mm"),
                "irrigation_week": m(row["irrigation_week"], "mm"),
                "irrigation_cum": m(row["irrigation_cum"], "mm"),
                "salinity": sal,
            }
        )
    return {
        "member": member,
        "analog_year": identity["year"],
        **({"member_label": identity["member_label"]} if "member_label" in identity else {}),
        "members": stored["members"],
        "step": "week",
        "events": stored["events"],
        "series": series,
    }


# ---------- orchestration ----------


def run_plan(
    field: dict, ctx: dict, state: dict, req: dict, override: dict | None = None, *, simulate
) -> dict:
    started = stage = perf_counter()
    timings = {}

    def timed(name):
        nonlocal stage
        now = perf_counter()
        timings[name] = round((now - stage) * 1000, 2)
        stage = now

    as_of = dt.date.fromisoformat(req["as_of"])
    region = ctx["region"]
    n = req.get("horizon_seasons", 3)
    constraints = req.get("constraints") or {}
    windows = window_instances(region, as_of, n)
    gates = [{"gate": "G1", "passed": True, "message": "Đã xác định thửa và vùng."}]
    baseline_crops = req.get("baseline") or field["profile"].get("baseline")
    if not baseline_crops:
        baseline_crops = ["rice"] * n
        gates.append(
            {
                "gate": "G2",
                "passed": False,
                "message": "Chưa biết chuỗi hiện tại; dùng baseline GIẢ ĐỊNH lúa liên tục.",
            }
        )
    else:
        gates.append({"gate": "G2", "passed": True, "message": "Đã có chuỗi hiện tại."})
    baseline_crops = (list(baseline_crops) + [baseline_crops[-1]] * n)[:n]
    unknown = [c for c in baseline_crops if c not in CROP_BY_ID]
    if unknown:
        raise ValueError(f"UNKNOWN_CROP:{unknown}")

    irr = constraints.get("irrigation") or field["profile"].get("irrigation", "full")
    cap = {"full": None, "rainfed": 0.0}.get(
        irr, constraints.get("irrigation_cap_mm") or DEFAULT_CANAL_CAP_MM
    )
    if override and override.get("irrigation_cap_mm") is not None:
        cap = override["irrigation_cap_mm"]
    max_dur = max(c["duration_days"]["max"] for c in CROPS["crops"])
    span = (windows[-1]["sow_to"] - as_of).days + max_dur + 5
    ev = Evaluator(ctx, state, field, as_of, span, cap, override, simulate=simulate)
    region = ev.region
    if not ev.scenarios:
        return {
            "insufficient": True,
            "year_outlook": ev.year_outlook,
            "gates": gates
            + [
                {
                    "gate": "G6",
                    "passed": False,
                    "message": "Không đủ dữ liệu lịch sử để tạo kịch bản.",
                }
            ],
        }
    scen = {s["scenario_id"]: s for s in ev.scenarios}
    timed("setup")

    sow_shift = (override or {}).get("sow_shift_days") or {}
    turnaround = region["min_turnaround_days"]

    def shifted(sows):
        return [
            (t, d + dt.timedelta(days=int(sow_shift.get(str(i + 1), 0))))
            for i, (t, d) in enumerate(sows)
        ]

    std = [next(o for o in sow_options(w) if o[0] == "standard") for w in windows]
    # A chain evaluated on request may keep its own sow timings (e.g. an engine option sown early).
    base_timing = req.get("baseline_sow_timing")
    if base_timing:
        if len(base_timing) != n:
            raise ValueError("SOW_TIMING_LENGTH_MISMATCH")
        base_sows = []
        for w, t in zip(windows, base_timing):
            opt = next((o for o in sow_options(w) if o[0] == t), None)
            if opt is None:
                raise ValueError(f"SOW_TIMING_NOT_AVAILABLE:{w['id']}:{t}")
            base_sows.append(opt)
    else:
        base_sows = std
    base_seq = make_sequence(windows, baseline_crops, shifted(base_sows))
    candidates, excluded = [], []
    crop_ids = [c["id"] for c in CROPS["crops"]]
    max_changes = constraints.get(
        "max_changed_seasons", 1
    )  # UC-01: change at most one season by default
    max_fallow = constraints.get("max_fallow_seasons", 1)

    def allowed(crops):  # also valid for a prefix: zip stops at the shorter sequence
        return (
            sum(a != b for a, b in zip(crops, baseline_crops)) <= max_changes
            and crops.count("fallow_cover") <= max_fallow
        )

    screening = SCREENING_SCENARIOS | ({ENSO_SCENARIO_ID} & scen.keys())

    def evaluate(seq):
        res = ev.evaluate(seq, screening)
        summary = {sid: summarize(runs) for sid, runs in res.items()}
        rules = calendar_rules(seq, windows, turnaround) + field_rules(
            seq, ev, summary, constraints
        )
        c = {
            "seq": seq,
            "summary": summary,
            "rules": rules,
            "status": status_of(rules),
            "soil_indicators": soil_indicators(seq),
            "production_value_index": production_value_index(seq, region),
            "salinity_exposure": {
                "typical": salinity_exposure_days(seq, region, as_of, 0),
                "early_onset": salinity_exposure_days(seq, region, as_of, SALINITY_EARLY_WEEKS),
            },
        }
        return c

    if n <= EXHAUSTIVE_MAX_SEASONS:
        for crops in itertools.product(crop_ids, repeat=n):
            if not allowed(crops):
                continue
            for sows in itertools.product(*[sow_options(w) for w in windows]):
                seq = make_sequence(windows, crops, shifted(list(sows)))
                hard = calendar_rules(seq, windows, turnaround)
                if hard:
                    if len(excluded) < 400:
                        excluded.append((seq, hard))
                    continue
                candidates.append(seq)
    else:
        # Beam search: extend each kept prefix by one season, screen it on SCREENING_SCENARIOS
        # (carry-over included), keep the best sow timing per crop prefix, then the BEAM_WIDTH
        # prefixes with the least (irrigation clim + dry, then water + heat stress p90).
        # ponytail: one sow timing per crop prefix; widen if sow diversity matters for long horizons.
        beam = [((), ())]
        for w in windows:
            best = {}
            for crops, sows in beam:
                for crop in crop_ids:
                    if not allowed(crops + (crop,)):
                        continue
                    for sow in sow_options(w):
                        seq = make_sequence(windows, crops + (crop,), shifted([*sows, sow]))
                        p = evaluate(seq)
                        hard = [r for r in p["rules"] if r["severity"] == "HARD"]
                        if hard:
                            if len(excluded) < 400:
                                excluded.append((seq, hard))
                            continue
                        sm = p["summary"]
                        score = (
                            sm["sc_clim"]["irrigation_mm"]["p50"]
                            + sm[dry_scenario(sm)]["irrigation_mm"]["p50"],
                            sm["sc_clim"]["water_stress_days"]["p90"]
                            + sm["sc_clim"]["heat_stress_days_sensitive"]["p90"],
                        )
                        key = crops + (crop,)
                        if key not in best or score < best[key][0]:
                            best[key] = (score, (*sows, sow))
            ranked = sorted(best.items(), key=lambda kv: kv[1][0])[:BEAM_WIDTH]
            beam = [(crops, sows) for crops, (_, sows) in ranked]
        candidates = [make_sequence(windows, crops, shifted(list(sows))) for crops, sows in beam]

    timed("candidate_generation")

    base = evaluate(base_seq)
    base["crit"] = criteria(base, base)
    evaluated = []
    for seq in candidates:
        c = evaluate(seq)
        if c["status"] == "NOT_FEASIBLE":
            excluded.append((seq, [r for r in c["rules"] if r["severity"] == "HARD"]))
            continue
        c["crit"] = criteria(c, base)
        evaluated.append(c)
    timed("screening")
    front = pareto(evaluated)
    priorities = req.get("priorities") or ["avoid_crop_failure", "save_water", "soil_health"]
    picked = pick_strategies(
        front, base, priorities, evaluated, bool(state["coastal_salinity_risk"]["value"])
    )
    enso_driven = set()
    if ENSO_SCENARIO_ID in screening:
        # Same selection with the equal-weight dry criterion (sc_dry): strategies whose pick
        # differs were chosen because of the ENSO analog years, and the summary says so.
        def equal_weight(c):
            return {
                **c,
                "crit": {**c["crit"], "irr_dry": c["summary"]["sc_dry"]["irrigation_mm"]["p50"]},
            }

        eq_eval = [equal_weight(c) for c in evaluated]
        eq = dict(
            pick_strategies(
                pareto(eq_eval),
                base,
                priorities,
                eq_eval,
                bool(state["coastal_salinity_risk"]["value"]),
            )
        )
        enso_driven = {
            s
            for s, c in picked
            if s not in eq or eq[s]["seq"]["sequence_id"] != c["seq"]["sequence_id"]
        }
    timed("selection")

    # The shortlist is fixed using exactly the same criteria and candidate order as before.
    # Extra scenarios and display distributions are needed only for returned sequences.
    chosen = [base] + [c for _, c in picked]
    for c in chosen:
        res = ev.evaluate(c["seq"])
        c["summary"] = {sid: summarize(runs) for sid, runs in res.items()}
        c["distribution"] = distribution_view(res, scen, c["summary"])
    timed("selected_scenarios")

    # gates
    coastal = state["coastal_salinity_risk"]["value"]
    gates.append(
        {
            "gate": "G3",
            "passed": True,
            "message": f"Catalog {CROPS['version']}: {number_vi(len(crop_ids))} lựa chọn có tham số.",
        }
    )
    if any(r["rule_id"] == "R_DRAINAGE_UNKNOWN" for _, c in picked for r in c["rules"]):
        gates.append(
            {
                "gate": "G4",
                "passed": False,
                "message": "Chưa xác nhận thoát nước cho cây cạn → phương án có điều kiện.",
            }
        )
    if coastal and state["canal_ecw"]["value"] is None:
        gates.append(
            {
                "gate": "G5",
                "passed": False,
                "message": "Vùng có rủi ro mặn nhưng chưa đo ECw nước kênh; không khẳng định an toàn mặn.",
            }
        )
    gates.append(
        {
            "gate": "G6",
            "passed": "sc_forecast" in scen,
            "message": (
                "Seasonal forecast present and fresh; skill not evaluated for Mekong."
                if "sc_forecast" in scen
                else "Forecast unavailable/stale; skill not evaluated for Mekong. Using climatology + stress tests."
            ),
        }
    )
    gates.append(
        {
            "gate": "G7",
            "passed": False,
            "message": "Chưa có mô hình năng suất/lợi nhuận đã hiệu chỉnh → chỉ so sánh nước, stress, lịch và lợi ích đất tiềm năng.",
        }
    )

    # AC-06: a what-if sow shift recomputes every chain; say so where the change is explained.
    def shift_note(seq):
        text = "; ".join(
            f"Vụ {number_vi(s['index'])} gieo {'sớm' if days < 0 else 'muộn'} {number_vi(abs(days))} ngày theo giả định (ngày gieo {s['sow']})"
            for s in seq["seasons"]
            if (days := int(sow_shift.get(str(s["index"]), 0)))
        )
        return text + "." if text else ""

    def view(c, strategy=None):
        shift_text = shift_note(c["seq"])
        metrics, delta = metrics_view(c["summary"], None if c is base else base["summary"], scen)
        seq = c["seq"]
        out = {
            "sequence_id": seq["sequence_id"],
            "is_baseline": c is base,
            "strategy_tag": strategy,
            "strategy_name_vi": STRATEGY_VI.get(strategy),
            "decision_status": c["status"] if c is not base else c["status"],
            "seasons": [
                {**s, "sow": str(s["sow"]), "harvest": str(s["harvest"])} for s in seq["seasons"]
            ],
            "metrics": metrics,
            "distribution": c["distribution"],
            "delta_vs_baseline": delta,
            "production_value_index": c["production_value_index"],
            "salinity_exposure_days": {
                "option": c["salinity_exposure"]["typical"],
                "baseline": base["salinity_exposure"]["typical"],
            },
            "soil_benefit": {
                "claim_type": "POTENTIAL_QUALITATIVE",
                "value": None,
                "indicators": c["soil_indicators"],
            },
            "rules": c["rules"],
        }
        if strategy == "salinity_avoidance":
            out["salinity_overlap_avoided_days"] = salinity_avoided(c, base)
        out.update(
            explain(c, base, ev, strategy)
            if c is not base
            else {
                "reasons": [],
                "risks": [
                    {
                        "code": r["rule_id"],
                        "severity": r["severity"],
                        "season_index": r["season_index"],
                        "text": r["reason"],
                    }
                    for r in c["rules"]
                ],
                "triggers": explain(c, base, ev)["triggers"],
                "checklist": [],
            }
        )
        robust = None if c is base else robustness(c, base)
        out["robustness"] = robust
        out["confidence"] = confidence(c, robust, state, scen)
        for sid in (robust or {}).get("lost_scenarios", []):
            if scen[sid]["kind"] in OUTLOOK_KINDS:
                out["risks"].append(
                    {
                        "code": "R_OUTLOOK_REVERSAL",
                        "severity": "SOFT",
                        "season_index": None,
                        "text": f"Kịch bản {SCENARIO_PRESENTATION[scen[sid]['kind']][1]} ({scen[sid]['name']}): phương án không đồng thời giảm nước tưới và không tăng ngày stress so với hiện tại",
                    }
                )
        if shift_text:
            out["reasons"].append({"text": shift_text, "evidence_ids": ["ev_region_calendar"]})
        enso_text = ""
        if strategy in enso_driven:
            yo = ev.year_outlook
            enso_text = (
                f"Thứ tự phương án thay đổi khi tiêu chí năm khô"
                f" dùng tín hiệu thống kê ENSO ({', '.join(yo['analog_labels_vi'])}; chênh lệch stress nhỏ, có thể do phá hòa; chưa chứng minh lợi thế tưới)."
            )
            out["reasons"].append({"text": enso_text, "evidence_ids": list(yo["evidence_ids"])})
        # Keep the team value heuristic last, including additional what-if/ENSO notes.
        out["reasons"].sort(key=lambda r: "ev_value_heuristic" in r.get("evidence_ids", []))
        if c is not base:
            pairs = list(zip(seq["seasons"], base["seq"]["seasons"]))
            changes = [
                f"Đổi vụ {s['window_name_vi']} sang {s['crop_name_vi']}"
                for s, b in pairs
                if s["crop"] != b["crop"]
            ] or [
                f"Gieo đầu khung vụ {s['window_name_vi']}" for s, b in pairs if s["sow"] < b["sow"]
            ]
            summary = "; ".join(changes) + ": " + out["reasons"][0]["text"]
            if any(r["rule_id"] == "R_DRAINAGE_UNKNOWN" for r in c["rules"]):
                summary = summary.rstrip(".") + "; cần xác nhận thoát nước."
            if shift_text:
                summary = summary.rstrip(".") + ". " + shift_text
            if enso_text:
                summary = summary.rstrip(".") + ". " + enso_text
            out["summary_vi"] = summary
        return out

    timed("explanation_setup")
    trajectories, member_trajectories = {}, {}
    end = max(s["harvest"] for c in chosen for s in c["seq"]["seasons"])
    for c in chosen:
        sequence_id = c["seq"]["sequence_id"]
        member_trajectories[sequence_id] = {
            sid: trajectory_members(ev, c, s, end) for sid, s in scen.items()
        }
        trajectories[sequence_id] = {
            sid: trajectory(stored) for sid, stored in member_trajectories[sequence_id].items()
        }

    timed("trajectories")
    seen_ex = {}
    for seq, rules in excluded:
        key = (tuple(seq["crops"]), rules[0]["rule_id"])
        if key not in seen_ex:
            seen_ex[key] = {
                "sequence_id": seq["sequence_id"],
                "crops": seq["crops"],
                **{
                    k: rules[0][k]
                    for k in ("rule_id", "severity", "reason", "inputs_used", "how_to_resolve")
                },
            }
    notes = list(ctx.get("outlook_notes", []))
    if len(picked) < 2:
        notes.append(
            "Không đủ hai phương án thay thế khả thi khác biệt; không bịa thêm ứng viên (AC-01)."
        )
    active_lo, active_hi = salinity_window(region, as_of, 0)
    typical_lo, typical_hi = salinity_window(ctx["region"], as_of, 0)
    result = {
        "source_conflicts": ctx.get("source_conflicts", []),
        "salinity_window": {
            "start": str(active_lo),
            "end": str(active_hi),
            "typical_start": str(typical_lo),
            "typical_end": str(typical_hi),
            "adjusted": ev.salinity_adjusted,
            "kind": "ASSUMPTION",
            "evidence_ids": ["ev_salinity_season"]
            + (["ev_siwrr_2026_press"] if ev.salinity_adjusted else []),
        },
        "gates": gates,
        "windows": [
            {**w, "sow_from": str(w["sow_from"]), "sow_to": str(w["sow_to"])} for w in windows
        ],
        "scenarios": [
            # Contract: the ENSO analog scenario also lists its members ([{year}]).
            {k: v for k, v in s.items() if k != "members" or s["scenario_id"] == ENSO_SCENARIO_ID}
            | {"analog_years": sorted({m["year"] for m in s["members"]})}
            for s in ev.scenarios
        ],
        "baseline": view(base),
        "options": [view(c, s) for s, c in picked],
        "excluded": list(seen_ex.values())[:30],
        "stats": {
            "generated": len(candidates) + len(excluded),
            "calendar_feasible": len(candidates),
            "evaluated_feasible": len(evaluated),
            "pareto_front": len(front),
            "season_simulations": len(ev.memo),
            "timings_ms": timings,
        },
        "irrigation_cap_mm_per_season": cap,
        "year_outlook": ev.year_outlook,
        "trajectories": trajectories,
        "member_trajectories": member_trajectories,
        "notes": notes,
    }
    timed("packaging")
    timings["total"] = round((perf_counter() - started) * 1000, 2)
    return result
