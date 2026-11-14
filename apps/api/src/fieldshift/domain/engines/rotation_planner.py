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
    build_scenarios,
    build_weather,
    dry_season_rain,
)
from fieldshift.domain.formatting import number_vi
from fieldshift.domain.value_objects.measure import measure

VERSIONS = {
    "catalog": CROPS["version"],
    "rules": "rules-1",
    "water_model": "fao56-v1",
    "planner": "pareto-v1",
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
}
# criteria() reads climate/dry summaries; field_rules() reads climate only.
# Keep this set aligned with those dependencies so optional outlooks cannot change selection.
SCREENING_SCENARIOS = frozenset({"sc_clim", "sc_dry"})


# ---------- season windows & generator ----------


def _md(year: int, mmdd: str) -> dt.date:
    m, d = map(int, mmdd.split("-"))
    return dt.date(year, m, d)


def window_instances(region: dict, as_of: dt.date, n: int) -> list[dict]:
    out = []
    for y in range(as_of.year - 1, as_of.year + 3):
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
            return lo + dt.timedelta(weeks=shift_weeks), hi
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
    }


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
        self.scenarios = build_scenarios(ctx, as_of, span_days, override)
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

    def season(self, crop_id, sow, key, dep):
        k = (crop_id, sow, self.simulation_keys[key], round(dep, 1))
        if k not in self.memo:
            r = self.simulate(
                self.weather[key],
                CROP_BY_ID[crop_id],
                sow,
                self.lat,
                self.elev,
                self.region["paddy"],
                self.soil,
                round(dep, 1),
                self.cap,
            )
            self.memo[k] = r
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
        for s in seq["seasons"]:
            r = self.season(s["crop"], s["sow"], key, dep)
            out.append(r)
            dep = r["end_state"]["depletion_frac"]  # inter-season water carry-over (AC-05)
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
    early_lo, _ = salinity_window(region, ev.as_of, -4)
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
            if ov_early >= 7:
                thr = c["salinity"]["ecw_threshold_ds_m"]
                if ecw is None:
                    rules.append(
                        rule(
                            "R_SALINITY_UNKNOWN",
                            "UNKNOWN_REQUIRES_CHECK",
                            i,
                            f"Vụ {number_vi(i)} ({c['name_vi']}) trùng mùa mặn {number_vi(ov)} ngày ({number_vi(ov_early)} ngày nếu mặn đến sớm 4 tuần); chưa đo ECw nước kênh",
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
        if ps["heat_stress_days_sensitive"] >= 5:
            rules.append(
                rule(
                    "R_HEAT",
                    "SOFT",
                    i,
                    f"{c['name_vi']}: trung vị {number_vi(ps['heat_stress_days_sensitive'])} ngày Tmax ≥ {number_vi(c['heat']['tmax_threshold_c'])} °C ở giai đoạn nhạy cảm",
                    ["NASA POWER T2M_MAX", "crops.heat"],
                    "Dời ngày gieo để giai đoạn nhạy cảm tránh tháng nóng",
                    ["ev_power_daily", "ev_crop_catalog"],
                )
            )
        if ps["water_stress_days"] >= 7:
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
            and ps["rain_mm"] >= 600
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


def criteria(c, baseline):
    s = c["summary"]
    return {
        "irr": s["sc_clim"]["irrigation_mm"]["p50"],
        "irr_dry": s["sc_dry"]["irrigation_mm"]["p50"],
        "stress_p90": s["sc_clim"]["water_stress_days"]["p90"]
        + s["sc_clim"]["heat_stress_days_sensitive"]["p90"],
        "salt": sum(1 for r in c["rules"] if r["rule_id"].startswith("R_SALINITY")),
        "soil": -len(c["soil_indicators"]),
        "changes": sum(1 for a, b in zip(c["seq"]["crops"], baseline["seq"]["crops"]) if a != b),
        "idle": c["seq"]["crops"].count("fallow_cover"),
    }


def pareto(cands):
    keys = ["irr", "irr_dry", "stress_p90", "salt", "soil", "changes", "idle"]
    front = []
    for a in cands:
        if not any(
            all(b["crit"][k] <= a["crit"][k] for k in keys)
            and any(b["crit"][k] < a["crit"][k] for k in keys)
            for b in cands
            if b is not a
        ):
            front.append(a)
    return front


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


def pick_strategies(front, baseline, priorities):
    pool = [c for c in front if c["seq"]["crops"] != baseline["seq"]["crops"]]
    by = {
        "save_water": lambda c: (c["crit"]["idle"], c["crit"]["irr"], c["crit"]["irr_dry"]),
        "low_risk": lambda c: (
            c["crit"]["salt"],
            c["crit"]["idle"],
            c["crit"]["stress_p90"],
            c["crit"]["irr_dry"],
        ),
        "soil_support": lambda c: (c["crit"]["soil"], c["crit"]["irr"]),
        "balanced": lambda c: (c["crit"]["changes"], c["crit"]["stress_p90"], c["crit"]["irr"]),
    }
    order = strategy_order(priorities)
    picked, used = [], set()
    for s in by:  # assign in fixed order so labels don't depend on priorities; priorities only reorder (§6.7.4)
        for c in sorted(pool, key=by[s]):
            sig = tuple(c["seq"]["crops"])
            if sig not in used:  # no near-duplicates (same crops, different sow date)
                used.add(sig)
                picked.append((s, c))
                break
    return sorted(picked, key=lambda x: order.index(x[0]))[:4]


# ---------- explanation ----------


def explain(c, base, ev) -> dict:
    s, b = c["summary"]["sc_clim"], base["summary"]["sc_clim"]
    sd, bd = c["summary"]["sc_dry"], base["summary"]["sc_dry"]
    reasons = []
    d = s["irrigation_mm"]["p50"] - b["irrigation_mm"]["p50"]
    if d <= -50:
        reasons.append(
            {
                "text": f"Nhu cầu tưới trung vị giảm ~{number_vi(-d)} mm (~{number_vi(-d * 10)} m³/ha) so với hiện tại trên cùng {number_vi(s['members'])} năm lịch sử NASA POWER.",
                "evidence_ids": ["ev_power_daily", "ev_crop_catalog"],
            }
        )
    dd = sd["irrigation_mm"]["p50"] - bd["irrigation_mm"]["p50"]
    if dd <= -50:
        reasons.append(
            {
                "text": f"Trong các năm khô nhất, giảm ~{number_vi(-dd)} mm nước tưới so với hiện tại.",
                "evidence_ids": ["ev_power_daily"],
            }
        )
    ds = s["heat_stress_days_sensitive"]["p50"] - b["heat_stress_days_sensitive"]["p50"]
    if ds <= -3:
        reasons.append(
            {
                "text": f"Giảm ~{number_vi(-ds)} ngày nắng nóng (≥ ngưỡng cây) ở giai đoạn nhạy cảm.",
                "evidence_ids": ["ev_power_daily", "ev_crop_catalog"],
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
        "reasons": reasons[:3],
        "risks": risks,
        "triggers": triggers,
        "checklist": list(dict.fromkeys(checklist)),
    }


def metrics_view(summary: dict, base_summary: dict | None, scen: dict) -> tuple[dict, dict]:
    metrics, delta = {}, {}
    for sid, s in summary.items():
        label = "Dự kiến" if scen[sid]["kind"] == "CLIMATOLOGY" else "Kịch bản"
        origin = "inferred_by_model" if label == "Dự kiến" else "assumed_scenario"

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
        weather = {w["date"]: w for w in ev.weather[(sid, i)]}
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
            rain = sum(
                weather.get(date + dt.timedelta(days=d), {}).get("rain_mm", 0) or 0
                for d in range(min(7, (end - date).days + 1))
            )
            ks = min((row["ks"] for _, row in active), default=1)
            series.append(
                {
                    "date": str(date),
                    "season_index": season["index"] if season else None,
                    "crop": season["crop"] if season else None,
                    "stage": water.get("stage"),
                    "root_depth_m": water.get("root_depth_m"),
                    "root_zone_water": water.get("root_zone_water"),
                    "ponding_mm": water.get("ponding_mm"),
                    "rain_week": round(rain, 1),
                    "irrigation_week": round(irrigation, 1),
                    "irrigation_cum": round(cum),
                    "stress_risk": "HIGH" if ks < 0.6 else "MEDIUM" if ks < 1 else "LOW",
                }
            )
        compare_series_by_member.append(series)
        native = []
        for season, result in zip(c["seq"]["seasons"], seasons):
            cum = 0.0
            for week in result["season_weeks"]:
                cum += week["irrigation_week"]
                ks = week["ks"]
                native.append(
                    {
                        **{k: v for k, v in week.items() if k != "ks"},
                        "season_index": season["index"],
                        "crop": season["crop"],
                        "irrigation_week": round(week["irrigation_week"], 1),
                        "irrigation_cum": round(cum),
                        "stress_risk": "HIGH" if ks < 0.6 else "MEDIUM" if ks < 1 else "LOW",
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
    origin = "inferred_by_model" if stored["kind"] == "CLIMATOLOGY" else "assumed_scenario"
    label = "Dự kiến" if stored["kind"] == "CLIMATOLOGY" else "Kịch bản"

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
                "root_zone_water": measure(
                    row["root_zone_water"],
                    "fraction",
                    "inferred_by_model",
                    "Dự kiến",
                    stored["evidence_ids"],
                    reason="NO_ACTIVE_CROP",
                ),
                "ponding_mm": m(
                    row["ponding_mm"], "mm", "NOT_PADDY" if row["crop"] else "NO_ACTIVE_CROP"
                ),
                "root_depth_m": m(row["root_depth_m"], "m", "NO_ACTIVE_CROP"),
                "rain_week": measure(
                    row["rain_week"], "mm", "assumed_scenario", "Kịch bản", stored["evidence_ids"]
                ),
                "irrigation_week": m(row["irrigation_week"], "mm"),
                "irrigation_cum": measure(
                    row["irrigation_cum"],
                    "mm",
                    "inferred_by_model",
                    "Dự kiến",
                    stored["evidence_ids"],
                ),
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
    if not ev.scenarios:
        return {
            "insufficient": True,
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
    for crops in itertools.product(crop_ids, repeat=n):
        if (
            sum(a != b for a, b in zip(crops, baseline_crops)) > max_changes
            or crops.count("fallow_cover") > max_fallow
        ):
            continue
        for sows in itertools.product(*[sow_options(w) for w in windows]):
            seq = make_sequence(windows, crops, shifted(list(sows)))
            hard = calendar_rules(seq, windows, turnaround)
            if hard:
                if len(excluded) < 400:
                    excluded.append((seq, hard))
                continue
            candidates.append(seq)

    timed("candidate_generation")

    def evaluate(seq):
        res = ev.evaluate(seq, SCREENING_SCENARIOS)
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
        }
        return c

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
    picked = pick_strategies(front, base, priorities)
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

    def view(c, strategy=None):
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
            "soil_benefit": {
                "claim_type": "POTENTIAL_QUALITATIVE",
                "value": None,
                "indicators": c["soil_indicators"],
            },
            "rules": c["rules"],
        }
        out.update(
            explain(c, base, ev)
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
        if c is not base:
            changes = [
                f"Đổi vụ {s['window_name_vi']} sang {s['crop_name_vi']}"
                for s, b in zip(seq["seasons"], base["seq"]["seasons"])
                if s["crop"] != b["crop"]
            ]
            summary = "; ".join(changes) + ": " + out["reasons"][0]["text"]
            if any(r["rule_id"] == "R_DRAINAGE_UNKNOWN" for r in c["rules"]):
                summary = summary.rstrip(".") + "; cần xác nhận thoát nước."
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
    result = {
        "gates": gates,
        "windows": [
            {**w, "sow_from": str(w["sow_from"]), "sow_to": str(w["sow_to"])} for w in windows
        ],
        "scenarios": [
            {k: v for k, v in s.items() if k != "members"}
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
        "trajectories": trajectories,
        "member_trajectories": member_trajectories,
        "notes": notes,
    }
    timed("packaging")
    timings["total"] = round((perf_counter() - started) * 1000, 2)
    return result
