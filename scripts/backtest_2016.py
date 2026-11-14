"""Backtest: kế hoạch lập ở as_of 2015-11-15 / 2019-11-15 (chỉ dữ liệu < as_of) chấm bằng thời tiết THỰC của các vụ sau đó.

Chạy offline trên cache: PYTHONPATH=apps/api/src python scripts/backtest_2016.py  -> docs/BACKTEST_REPORT.md
Cùng mô hình nước (fao56_water.simulate_season) mô phỏng baseline và từng phương án trên thời tiết NASA POWER thực.
Không có quan trắc mặn -> mặn chỉ được đánh giá bằng mức trùng cửa sổ mùa mặn điển hình của vùng (logic của engine).
"""

import datetime as dt
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sensitivity  # noqa: E402  (reuses the offline clock/network patch and the temp data dir)
from fastapi.testclient import TestClient  # noqa: E402
from fieldshift.application.use_cases.plan_rotation import context_for  # noqa: E402
from fieldshift.domain.catalog import CROP_BY_ID, REGIONS  # noqa: E402
from fieldshift.domain.engines.rotation_planner import overlap_days, salinity_window  # noqa: E402
from fieldshift.infrastructure.crop_models.fao56_water import simulate_season, weather_from_power  # noqa: E402
from fieldshift.infrastructure.data_sources.nasa.power import load_power  # noqa: E402
from fieldshift.infrastructure.persistence import sqlite as db  # noqa: E402
from fieldshift.main import app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/BACKTEST_REPORT.md"
SITES = {
    "fld_cantho": "Cần Thơ (nội đồng)",
    "fld_soctrang": "Sóc Trăng (ven biển)",
    "fld_bentre": "Bến Tre (ven biển)",
}
AS_OFS = [dt.date(2015, 11, 15), dt.date(2019, 11, 15)]
CONFIGS = {
    "full": {},  # tưới đủ: không giới hạn nước tưới
    "canal_limited": {"constraints": {"irrigation": "canal_limited"}},  # trần 500 mm/vụ
}


def actual_sim(weather, field, ctx, plan, option):
    """Chạy lại các vụ của `option` trên thời tiết thực; trả tổng tưới / ngày thiếu nước / ngày nóng."""
    dep = plan["field_state"]["initial_depletion_frac"]["value"]
    cap = plan["irrigation_cap_mm_per_season"]
    region = REGIONS[field["region_id"]]
    elev = ctx["elevation_m"] if ctx["elevation_m"] is not None else ctx["grid_elevation_m"]
    tot = dict(irr=0.0, stress=0.0, heat=0.0, rain=0.0)
    for s in option["seasons"]:
        r = simulate_season(
            weather,
            CROP_BY_ID[s["crop"]],
            dt.date.fromisoformat(s["sow"]),
            field["lat"],
            elev,
            region["paddy"],
            {"taw_mm_per_m": region["soil_prior"]["taw_mm_per_m"]},
            round(dep, 1),
            cap,
        )
        dep = r["end_state"]["depletion_frac"]
        tot["irr"] += r["irrigation_mm"]
        tot["stress"] += r["water_stress_days"]
        tot["heat"] += r["heat_stress_days_sensitive"]
        tot["rain"] += r["rain_mm"]
    return tot


def salinity_exposure(option, region, as_of):
    lo, hi = salinity_window(region, as_of, 0)
    return sum(
        overlap_days(dt.date.fromisoformat(s["sow"]), dt.date.fromisoformat(s["harvest"]), lo, hi)
        for s in option["seasons"]
        if CROP_BY_ID[s["crop"]]["water_regime"] != "none"
    )


def dry_season_context(weather, as_of):
    """Mưa 15/11 -> 30/4 của mùa khô ngay sau as_of so với các năm trước (chỉ dữ liệu có sẵn)."""

    def total(y):
        a, b = dt.date(y, 11, 15), dt.date(y + 1, 4, 30)
        days = [w["rain_mm"] for w in weather if a <= w["date"] <= b and w["rain_mm"] is not None]
        return sum(days) if len(days) > 150 else None

    prior = [t for y in range(2001, as_of.year) if (t := total(y)) is not None]
    now = total(as_of.year)
    rank = sum(p < now for p in prior) / len(prior) if prior and now is not None else None
    return now, st.mean(prior) if prior else None, rank


def main() -> None:
    sensitivity.go_offline()
    L = ["# Backtest 2016 / 2020 (hindcast có kiểm soát)\n"]
    L.append(
        "Sinh tự động bởi `scripts/backtest_2016.py`. Kế hoạch lập tại `as_of` chỉ dùng dữ liệu < as_of "
        "(engine ép AC-04; forecast mùa và CMIP6 tắt ở hindcast), horizon 3 vụ, ràng buộc mặc định. "
        "Sau đó baseline và từng phương án được mô phỏng lại bằng CÙNG mô hình nước FAO-56 trên thời tiết NASA POWER **thực** "
        "của các vụ đó. Hai cấu hình nước: `full` (tưới đủ) và `canal_limited` (trần 500 mm/vụ, để ngày thiếu nước có ý nghĩa).\n"
    )
    verdict_rows, better, total = [], 0, 0
    flagged_sal = cases = 0
    flags = {}  # (site, cfg) -> {year: rule-set} to see whether flags tell a record-dry year from a normal one
    with TestClient(app) as client:
        for fid, site in SITES.items():
            field = db.get(db.connect(), "fields", fid)
            payload, _ = load_power(field["lat"], field["lon"], field["profile"].get("cache_key"))
            weather = weather_from_power(payload)
            region = REGIONS[field["region_id"]]
            for as_of in AS_OFS:
                ctx = context_for(field, as_of)
                now, mean_rain, rank = dry_season_context(weather, as_of)
                for cfg, extra in CONFIGS.items():
                    r = client.post(
                        "/v1/plans", json={"field_id": fid, "as_of": str(as_of), **extra}
                    )
                    assert r.status_code == 201, r.text
                    plan = r.json()
                    base = plan["baseline"]
                    act = {
                        o["sequence_id"]: actual_sim(weather, field, ctx, plan, o)
                        for o in [base, *plan["options"]]
                    }
                    ba = act[base["sequence_id"]]
                    L.append(f"\n## {site} — as_of {as_of} — nước `{cfg}`\n")
                    L.append(
                        f"- Mưa 15/11–30/4 thực của mùa khô sau as_of: **{now:.0f} mm** (trung bình các năm trước {mean_rain:.0f} mm; "
                        f"khô hơn {1 - rank:.0%} số năm trước)."
                        if now is not None and rank is not None
                        else "- Không đủ dữ liệu mùa khô để xếp hạng năm."
                    )
                    rules = sorted({x["rule_id"] for x in base["rules"]})
                    sc = {s["scenario_id"] for s in plan["scenarios"]}
                    dry = base["metrics"].get("sc_dry", {})
                    L.append(
                        f"- Engine tại as_of: baseline `{base['decision_status']}`; luật kích hoạt: {', '.join(rules) or 'không'}; "
                        f"kịch bản: {', '.join(sorted(sc))}; cổng: "
                        + ", ".join(
                            f"{g['gate']}={'ok' if g['passed'] else 'FAIL'}" for g in plan["gates"]
                        )
                        + "."
                    )
                    if dry:
                        L.append(
                            f"- Dự báo của engine (baseline): nhu cầu tưới năm thường {base['metrics']['sc_clim']['irrigation_need']['value']} mm, "
                            f"năm hạn {dry['irrigation_need']['value']} mm; thiếu nước {dry['water_stress_days']['value']} ngày. "
                            f"**Thực tế** (mô phỏng thời tiết thực): tưới {ba['irr']:.0f} mm, thiếu nước {ba['stress']:.0f} ngày, nóng {ba['heat']:.0f} ngày."
                        )
                    cases += 1
                    flags.setdefault((site, cfg), {})[as_of.year] = (frozenset(rules), now)
                    flagged_sal += any(r_.startswith("R_SALINITY") for r_ in rules)
                    L.append(
                        "\n| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |"
                    )
                    L.append("|---|---|---|---|---|---|---|---|---|")
                    L.append(
                        f"| baseline | {'/'.join(s['crop'] for s in base['seasons'])} | {base['decision_status']} | 0 | 0 | {ba['irr']:.0f} | 0 | "
                        f"{salinity_exposure(base, region, as_of)} | - |"
                    )
                    for o in plan["options"]:
                        a = act[o["sequence_id"]]
                        pd = o["delta_vs_baseline"]["sc_clim"]["irrigation_need"]["value"]
                        di, ds = a["irr"] - ba["irr"], a["stress"] - ba["stress"]
                        ok = di <= 0 and ds <= 0 and (di < 0 or ds < 0)
                        tie = di == 0 and ds == 0
                        total += 1
                        better += ok
                        L.append(
                            f"| {o['strategy_tag']} | {'/'.join(s['crop'] for s in o['seasons'])} | {o['decision_status']} | {pd:+.0f} | {di:+.0f} | {a['irr']:.0f} | {ds:+.1f} | "
                            f"{salinity_exposure(o, region, as_of)} | {'có' if ok else 'hòa' if tie else 'KHÔNG'} |"
                        )
                        verdict_rows.append(
                            (site, as_of.year, cfg, o["strategy_tag"], pd, di, ds, ok)
                        )

    L.append("\n## Kết luận (số liệu, không tô vẽ)\n")
    L.append(
        f"- Phương án tốt hơn baseline TRONG năm thực (tưới ít hơn và thiếu nước không nhiều hơn, ít nhất một chiều nghiêm ngặt): **{better}/{total}**."
    )
    nz = [r for r in verdict_rows if r[4] != 0]
    agree = sum((r[4] < 0) == (r[5] < 0) for r in nz)
    L.append(
        f"- Dấu của Δtưới dự kiến trùng với Δtưới thực: **{agree}/{len(nz)}** phương án (trung vị nhiều năm so với một năm thực; chủ yếu do màu cạn dùng ít nước hơn lúa trong mô hình)."
    )
    worse = [f"{r[0]} {r[1]} {r[2]} {r[3]}" for r in verdict_rows if not r[7]]
    L.append(
        f"- Phương án KHÔNG tốt hơn baseline ({len(worse)}): "
        + ("; ".join(worse) or "không có")
        + ". Trong mô hình, `fallow_cover` không được tưới nên tăng số ngày thiếu nước khi tưới đủ."
    )
    same = sum(len({v[0] for v in d.values()}) == 1 for d in flags.values())
    L.append(
        f"- Cờ rủi ro của engine tại as_of GIỐNG HỆT nhau giữa năm 2015 (mùa khô thực rất khô) và 2019 ở **{same}/{len(flags)}** cặp (điểm × cấu hình nước). "
        "Hindcast không có forecast mùa nên engine chỉ có khí hậu nhiều năm: nó không phân biệt được năm cực khô với năm thường tại thời điểm lập kế hoạch."
    )
    L.append(
        f"- Cờ mặn R_SALINITY* trên baseline: {flagged_sal}/{cases} ca (đúng các ca ven biển; luôn bật vì lúa trùng mùa mặn điển hình, không dựa vào năm thực). Không có quan trắc để biết năm đó mặn thật hay không."
    )
    L.append(
        "- Điều backtest KHÔNG chứng minh: lợi ích về năng suất/thu nhập (mô hình chưa hiệu chỉnh, gate G7) hay giảm thiệt hại do mặn. "
        "'Tốt hơn' ở đây chỉ nghĩa là tiết kiệm nước tưới theo mô hình FAO-56 của chính engine."
    )
    if better < total / 2:
        L.append("- **Engine KHÔNG chứng minh được lợi ích** trong đa số ca backtest này.")
    L.append("\n## Hạn chế\n")
    L.append(
        "- Không có quan trắc độ mặn/ECw: không thể chấm rủi ro mặn thật; chỉ so mức trùng cửa sổ mùa mặn điển hình (logic engine).\n"
        "- NASA POWER là lưới ~50 km (có thể lẫn biển ở ô ven biển); mưa/ET0 không phải đo tại ruộng.\n"
        "- Chấm điểm dùng chính mô hình nước FAO-56 của engine (chưa hiệu chỉnh, G7): đây là nhất quán nội bộ, KHÔNG phải kiểm chứng với năng suất/nước tưới đo thực.\n"
        "- Một năm thực cho mỗi điểm: không có ý nghĩa thống kê; hai as_of × ba điểm × hai cấu hình là các ca không độc lập.\n"
        "- Trần tưới `canal_limited` 500 mm/vụ là giả định mặc định của engine, không phải số đo.\n"
    )
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUT.relative_to(ROOT)}; better={better}/{total}; flagged_sal={flagged_sal}/{cases}"
    )


if __name__ == "__main__":
    main()
