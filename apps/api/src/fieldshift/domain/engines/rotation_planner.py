"""Candidate Generator, Feasibility, Response evaluation, Risk-aware Planner, Explanation, Twin.

Design v2 §6.4–6.8. The planner never produces a single "science score" for display: it keeps the
Pareto front and picks diverse strategies; farmer priorities only order the presentation.
"""

import datetime as dt
import itertools
import statistics as st

from fieldshift.domain.catalog import CROP_BY_ID, CROPS
from fieldshift.domain.engines.future_outlook import build_scenarios, build_weather
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
                    f"Thu hoạch {a['crop_name_vi']} ({a['harvest']}) + {turnaround} ngày làm đất vượt ngày gieo vụ {b['index']} ({b['sow']})",
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
        self.weather = {}
        for s in self.scenarios:
            for i, m in enumerate(s["members"]):
                self.weather[(s["scenario_id"], i)] = build_weather(
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
        self.soil = {"taw_mm_per_m": self.region["soil_prior"]["taw_mm_per_m"]}
        self.memo = {}

    def season(self, crop_id, sow, key, dep, daily=False):
        k = (crop_id, sow, key, round(dep, 1), daily)
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
            if not daily:
                r = {x: v for x, v in r.items() if x != "daily"}
            self.memo[k] = r
        return self.memo[k]

    def run(self, seq, key, daily=False):
        dep = self.state["initial_depletion_frac"]["value"]
        out = []
        for s in seq["seasons"]:
            r = self.season(s["crop"], s["sow"], key, dep, daily)
            out.append(r)
            dep = r["end_state"]["depletion_frac"]  # inter-season water carry-over (AC-05)
        return out

    def evaluate(self, seq) -> dict:
        res = {}
        for s in self.scenarios:
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
                            f"Vụ {i} ({c['name_vi']}) trùng mùa mặn {ov} ngày ({ov_early} ngày nếu mặn đến sớm 4 tuần); chưa đo ECw nước kênh",
                            ["state.canal_ecw", "regions.salinity_season", "crops.salinity"],
                            f"Đo ECw nước kênh trước ngày gieo; ngưỡng tham khảo của {c['name_vi']} ≈ {thr} dS/m",
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
                            f"ECw đo được {ecw} dS/m > ngưỡng {thr} dS/m của {c['name_vi']}; giảm năng suất tham khảo ~{min(100, round(loss))}% (Maas-Hoffman, ECe≈1.5·ECw)",
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
                    f"{c['name_vi']}: trung vị {ps['heat_stress_days_sensitive']} ngày Tmax ≥ {c['heat']['tmax_threshold_c']} °C ở giai đoạn nhạy cảm",
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
                    f"{c['name_vi']}: trung vị {ps['water_stress_days']} ngày thiếu nước với nguồn tưới đã khai báo",
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
                    f"{c['name_vi']} chịu úng kém; mưa trung vị trong vụ {ps['rain_mm']} mm",
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
                "text": f"Nhu cầu tưới trung vị giảm ~{-d} mm (~{-d * 10:,} m³/ha) so với hiện tại trên cùng {s['members']} năm lịch sử NASA POWER.",
                "evidence_ids": ["ev_power_daily", "ev_crop_catalog"],
            }
        )
    dd = sd["irrigation_mm"]["p50"] - bd["irrigation_mm"]["p50"]
    if dd <= -50:
        reasons.append(
            {
                "text": f"Trong các năm khô nhất, giảm ~{-dd} mm nước tưới so với hiện tại.",
                "evidence_ids": ["ev_power_daily"],
            }
        )
    ds = s["heat_stress_days_sensitive"]["p50"] - b["heat_stress_days_sensitive"]["p50"]
    if ds <= -3:
        reasons.append(
            {
                "text": f"Giảm ~{-ds:g} ngày nắng nóng (≥ ngưỡng cây) ở giai đoạn nhạy cảm.",
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
                    "condition": f"ECw nước kênh > {thr} dS/m (≈ {thr * PPT_PER_DS_M:.1f} ‰) trước {season['sow']}",
                    "measure": "ECw nước kênh (máy đo EC cầm tay)",
                    "variable": "canal_ecw",
                    "op": "gt",
                    "threshold": thr,
                    "season_index": r["season_index"],
                    "unit": "dS/m",
                    "action": f"Không gieo {crop['name_vi']} vụ {r['season_index']}; tái lập kế hoạch",
                }
            )
        if r["severity"] == "UNKNOWN_REQUIRES_CHECK":
            checklist.append(r["how_to_resolve"])
    for season in c["seq"]["seasons"]:
        crop = CROP_BY_ID[season["crop"]]
        if crop["requires_good_drainage"]:
            triggers.append(
                {
                    "condition": f"Thoát nước kém trước vụ {season['index']}",
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
                    "condition": f"ECw nước kênh > {threshold} dS/m trước {season['sow']}",
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


def trajectory(ev: Evaluator, c: dict, scen: dict, sal_shift: int) -> dict:
    sid = scen["scenario_id"]
    runs = [
        (i, sum(x["irrigation_mm"] for x in ev.run(c["seq"], (sid, i))))
        for i in range(len(scen["members"]))
    ]
    i_med = sorted(runs, key=lambda t: t[1])[len(runs) // 2][0]
    seasons = ev.run(c["seq"], (sid, i_med), daily=True)
    sal_lo, sal_hi = salinity_window(ev.region, ev.as_of, sal_shift)
    coastal = ev.state["canal_ecw"]
    series = []
    for s, r in zip(c["seq"]["seasons"], seasons):
        cum = 0.0
        daily = r["daily"]
        for k in range(0, len(daily), 7):
            wk = daily[k : k + 7]
            cum += sum(x["irrigation"] for x in wk)
            ks = min(x["ks"] for x in wk)
            d0 = wk[0]["date"]
            in_sal = ev.state["coastal_salinity_risk"]["value"] and sal_lo <= d0 <= sal_hi
            sal = (
                measure(coastal["value"], "dS/m", coastal["origin"], coastal["label"])
                if coastal["value"] is not None
                else measure(None, "dS/m", "unknown", "Chưa biết", reason="CANAL_ECW_NOT_MEASURED")
            )
            sal["in_salinity_season"] = bool(in_sal)
            series.append(
                {
                    "date": str(d0),
                    "season_index": s["index"],
                    "crop": s["crop"],
                    "stage": wk[0]["stage"],
                    "root_zone_water": measure(
                        round(st.mean(x["water_frac"] for x in wk), 2),
                        "fraction",
                        "inferred_by_model",
                        "Dự kiến",
                    ),
                    "rain_week": measure(
                        round(sum(x["rain"] for x in wk), 1), "mm", "assumed_scenario", "Kịch bản"
                    ),
                    "irrigation_cum": measure(round(cum), "mm", "inferred_by_model", "Dự kiến"),
                    "salinity": sal,
                    "stress_risk": "HIGH" if ks < 0.6 else "MEDIUM" if ks < 1 else "LOW",
                }
            )
    return {"analog_year": scen["members"][i_med]["year"], "step": "week", "series": series}


# ---------- orchestration ----------


def run_plan(
    field: dict, ctx: dict, state: dict, req: dict, override: dict | None = None, *, simulate
) -> dict:
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

    sow_shift = (override or {}).get("sow_shift_days") or {}
    turnaround = region["min_turnaround_days"]

    def shifted(sows):
        return [
            (t, d + dt.timedelta(days=int(sow_shift.get(str(i + 1), 0))))
            for i, (t, d) in enumerate(sows)
        ]

    std = [next(o for o in sow_options(w) if o[0] == "standard") for w in windows]
    base_seq = make_sequence(windows, baseline_crops, shifted(std))
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

    def evaluate(seq):
        res = ev.evaluate(seq)
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
    front = pareto(evaluated)
    priorities = req.get("priorities") or ["avoid_crop_failure", "save_water", "soil_health"]
    picked = pick_strategies(front, base, priorities)

    # gates
    coastal = state["coastal_salinity_risk"]["value"]
    gates.append(
        {
            "gate": "G3",
            "passed": True,
            "message": f"Catalog {CROPS['version']}: {len(crop_ids)} lựa chọn có tham số.",
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
        return out

    chosen = [base] + [c for _, c in picked]
    trajectories = {}
    for c in chosen:
        trajectories[c["seq"]["sequence_id"]] = {
            sid: trajectory(ev, c, s, s["salinity_shift_weeks"]) for sid, s in scen.items()
        }

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
    return {
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
        },
        "irrigation_cap_mm_per_season": cap,
        "trajectories": trajectories,
        "notes": notes,
    }
