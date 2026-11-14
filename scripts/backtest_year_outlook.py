"""Hindcast of the ENSO year outlook: does conditioning on ONI (known before sowing) help?

PYTHONPATH=apps/api/src python scripts/backtest_year_outlook.py  -> docs/YEAR_OUTLOOK_REPORT.md
For each site × as_of the plan is built twice from data < as_of: with the ENSO analog years
(engine default) and with ONI hidden (equal-weight engine, the pre-feature behaviour). The
actual next dry-season rain (IMERG + POWER) is then compared with the analog expectation, and
both top-1 options are re-simulated on the real POWER weather (same FAO-56 model).
"""

import datetime as dt
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sensitivity  # noqa: E402  (offline clock/network patch + temp data dir)
from backtest_2016 import actual_sim  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from fieldshift.api.schemas.requests import PlanRequest  # noqa: E402
from fieldshift.application.use_cases.plan_rotation import context_for  # noqa: E402
from fieldshift.domain.engines.field_state import estimate_state  # noqa: E402
from fieldshift.domain.engines.future_outlook import (  # noqa: E402
    monthly_from_daily,
    season_label,
    season_rain_mm,
)
from fieldshift.domain.engines.rotation_planner import run_plan  # noqa: E402
from fieldshift.domain.formatting import number_vi  # noqa: E402
from fieldshift.infrastructure.crop_models.fao56_water import (  # noqa: E402
    simulate_season,
    weather_from_power,
)
from fieldshift.infrastructure.data_sources.enso import latest_oni  # noqa: E402
from fieldshift.infrastructure.data_sources.nasa.imerg import load_imerg_monthly  # noqa: E402
from fieldshift.infrastructure.data_sources.nasa.power import load_power  # noqa: E402
from fieldshift.infrastructure.persistence import sqlite as db  # noqa: E402
from fieldshift.main import app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/YEAR_OUTLOOK_REPORT.md"
SITES = {
    "fld_cantho": "Cần Thơ",
    "fld_soctrang": "Sóc Trăng",
    "fld_bentre": "Bến Tre",
    "fld_chaudoc": "Châu Đốc",
}
BACKTEST_SITES = ("fld_cantho", "fld_soctrang", "fld_bentre")
# El Niño-ish autumns by the coordinator's SON value (2015, 2018, 2019, 2023) and La Niña
# autumns (2010, 2020); the phase actually used is the no-look-ahead ASO value.
AS_OFS = [dt.date(y, 11, 15) for y in (2010, 2015, 2018, 2019, 2020, 2023)]
TODAY = dt.date(2026, 11, 14)
FAR = dt.date(2100, 1, 1)  # scoring only: every completed season is visible


def mm(v):
    return "–" if v is None else number_vi(round(v))


def crops(option):
    return "/".join(s["crop"] for s in option["seasons"])


def plan(field, ctx, state, as_of):
    """Same request defaults as POST /v1/plans (e.g. no_new_machinery)."""
    req = PlanRequest(field_id=field["id"], as_of=as_of).model_dump(mode="json")
    return run_plan(field, ctx, state, req, simulate=simulate_season)


def both(field, as_of):
    """(plan with ENSO analogs, plan with ONI hidden = equal-weight engine, ctx, state)."""
    ctx = context_for(field, as_of)
    state = estimate_state(field, ctx, as_of, [])
    hidden = {**ctx, "enso": {**ctx["enso"], "latest": None}}
    return plan(field, ctx, state, as_of), plan(field, hidden, state, as_of), ctx, state


def pearson(pairs):
    return st.correlation(*zip(*pairs)) if len(pairs) >= 3 else None


def main() -> None:
    sensitivity.go_offline()
    L = ["# Năm ENSO và mùa khô — hindcast có kiểm soát\n"]
    L.append(
        "Sinh tự động bởi `scripts/backtest_year_outlook.py` (offline, dữ liệu bundled). Tại mỗi `as_of`, "
        "engine chỉ dùng ONI có cửa sổ 3 tháng **đã kết thúc trước tháng của as_of** (15/11 → tháng giữa 09 = ASO) "
        "và chỉ các mùa khô đã kết thúc trước as_of. Mỗi ca chạy hai lần: có năm tương tự ENSO (mặc định) và "
        "ẩn ONI (engine cũ, mọi năm như nhau). Sau đó so với mưa mùa khô THỰC (tháng 12–4) và mô phỏng lại "
        "phương án đứng đầu của mỗi engine trên thời tiết NASA POWER thực. Đây là liên hệ thống kê, **không phải dự báo**.\n"
    )
    with TestClient(app):
        conn = db.connect()
        fields = {
            fid: {**f, "profile": {k: v for k, v in f["profile"].items() if v is not None}}
            for fid in SITES
            if (f := db.get(conn, "fields", fid))
        }

    L.append(f"## 0. Mùa khô {season_label(TODAY.year)} cho 4 ruộng demo (as_of {TODAY})\n")
    L.append(
        "| Ruộng | Pha (ONI) | Năm tương tự | Mưa 12–4 tương tự / mọi năm (mm) | r | Top-1 trước (mọi năm như nhau) | Top-1 sau (ENSO) | Shortlist khác? |"
    )
    L.append("|---|---|---|---|---|---|---|---|")
    heads = []
    for fid, name in SITES.items():
        e, o, _, _ = both(fields[fid], TODAY)
        yo, rain = e["year_outlook"], e["year_outlook"]["dry_season_rain"]
        heads.append(f"- {name}: {yo['headline_vi']} ({yo['skill']['note_vi']})")
        L.append(
            f"| {name} | {yo['enso']['phase']} ({number_vi(yo['enso']['value'], 2)}) | {', '.join(yo['analog_labels_vi'])} | "
            f"{mm(rain['analog_median_mm'])} / {mm(rain['all_years_median_mm'])} | {number_vi(yo['skill']['correlation_r'], 2)} | "
            f"{o['options'][0]['strategy_tag']} {crops(o['options'][0])} | {e['options'][0]['strategy_tag']} {crops(e['options'][0])} | "
            f"{'CÓ' if [x['sequence_id'] for x in e['options']] != [x['sequence_id'] for x in o['options']] else 'không'} |"
        )
    L.append("")
    L += heads
    L.append("")

    L.append("## 1. Tín hiệu: ONI (tháng giữa 09, không nhìn trước) và mưa tháng 12–4 sau đó\n")
    L.append("| Điểm | r (IMERG) | n | r (POWER) | n |")
    L.append("|---|---|---|---|---|")
    oni_now = latest_oni(TODAY)
    from fieldshift.infrastructure.data_sources.enso import load_oni

    oni = load_oni()
    for fid, name in SITES.items():
        f = fields[fid]
        payload, _ = load_power(f["lat"], f["lon"], f["profile"].get("cache_key"))
        power = monthly_from_daily([w for w in weather_from_power(payload) if w["date"] < TODAY])
        imerg = load_imerg_monthly(f["profile"].get("cache_key")) or {}
        row = []
        for monthly in (imerg, power):
            pairs = [
                (oni[(y, oni_now[1])], r)
                for y in range(2001, TODAY.year)
                if (r := season_rain_mm(monthly, y, TODAY)) is not None and (y, oni_now[1]) in oni
            ]
            r = pearson(pairs)
            row += [number_vi(round(r, 2), 2) if r is not None else "–", str(len(pairs))]
        L.append(f"| {name} | " + " | ".join(row) + " |")
    L.append(
        "\nr âm = ONI càng cao (El Niño) thì mùa khô sau đó càng ít mưa. n ≈ 24 mùa (2001–02…2024–25): "
        "tín hiệu đáng kể nhưng nhiều năm lệch.\n"
    )

    L.append("## 2. Hindcast theo năm\n")
    L.append(
        "| Điểm | as_of | ONI (tháng 09) | Pha | Năm tương tự | Kỳ vọng mưa 12–4: tương tự / mọi năm (mm) | "
        "Mưa thực IMERG / POWER (mm) | Top-1 có ENSO | Top-1 mọi năm như nhau | Shortlist khác? | "
        "Tưới thực top-1 ENSO / cũ (mm) |"
    )
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    stats = {"ok": 0, "dir_right": 0, "changed": 0, "cases": 0, "better": 0, "worse": 0}
    misses = []
    for fid in BACKTEST_SITES:
        f = fields[fid]
        payload, _ = load_power(f["lat"], f["lon"], f["profile"].get("cache_key"))
        weather = weather_from_power(payload)
        power_all = monthly_from_daily(weather)
        imerg_all = load_imerg_monthly(f["profile"].get("cache_key")) or {}
        for as_of in AS_OFS:
            with_enso, equal, ctx, state = both(f, as_of)
            yo = with_enso["year_outlook"]
            stats["cases"] += 1
            act_i = season_rain_mm(imerg_all, as_of.year, FAR)
            act_p = season_rain_mm(power_all, as_of.year, FAR)
            top_e, top_o = with_enso["options"][0], equal["options"][0]
            ids_e = [o["sequence_id"] for o in with_enso["options"]]
            ids_o = [o["sequence_id"] for o in equal["options"]]
            pl = {
                "field_state": state,
                "irrigation_cap_mm_per_season": with_enso["irrigation_cap_mm_per_season"],
            }
            irr_e = actual_sim(weather, f, ctx, pl, top_e)["irr"]
            irr_o = actual_sim(weather, f, ctx, pl, top_o)["irr"]
            enso = yo["enso"]
            rain = yo["dry_season_rain"]
            if yo["status"] == "OK":
                stats["ok"] += 1
                stats["changed"] += ids_e != ids_o
                stats["better"] += irr_e < irr_o
                stats["worse"] += irr_e > irr_o
                actual = act_i if act_i is not None else act_p
                exp_dry = rain["ratio"] is not None and rain["ratio"] < 1
                act_dry = actual is not None and actual < rain["all_years_median_mm"]
                stats["dir_right"] += exp_dry == act_dry
                if exp_dry != act_dry:
                    misses.append(
                        f"{SITES[fid]} {season_label(as_of.year)}: kỳ vọng {'khô' if exp_dry else 'ướt'} hơn thường "
                        f"(tương tự {mm(rain['analog_median_mm'])} mm, mọi năm {mm(rain['all_years_median_mm'])} mm), "
                        f"thực {mm(actual)} mm"
                    )
            L.append(
                f"| {SITES[fid]} | {as_of} | "
                + (f"{number_vi(enso['value'], 2)} | {enso['phase']}" if enso else "– | –")
                + f" | {', '.join(yo['analog_labels_vi']) or yo['reason']} | "
                f"{mm(rain['analog_median_mm'])} / {mm(rain['all_years_median_mm'])} | {mm(act_i)} / {mm(act_p)} | "
                f"{top_e['strategy_tag']} {crops(top_e)} | {top_o['strategy_tag']} {crops(top_o)} | "
                f"{'CÓ' if ids_e != ids_o else 'không'} | {mm(irr_e)} / {mm(irr_o)} |"
            )
            if fid == BACKTEST_SITES[0] and yo["status"] == "OK":
                L.append(f"|  | | | | _{yo['headline_vi']}_ | | | | | | |")

    L.append("\n## 3. Kết luận (số liệu, không tô vẽ)\n")
    L.append(
        f"- Có năm tương tự (status OK): **{stats['ok']}/{stats['cases']}** ca; còn lại UNAVAILABLE "
        "(< 3 năm cùng pha trong các năm lịch sử trước as_of; 2010 chỉ có 2001–2008) → engine y như cũ."
    )
    L.append(
        f"- Hướng mưa (khô/ướt hơn trung vị các năm trước) đúng ở **{stats['dir_right']}/{stats['ok']}** ca OK."
    )
    L.append("- Các ca trật: " + ("; ".join(misses) or "không có") + ".")
    L.append(
        f"- Shortlist khác engine cũ ở **{stats['changed']}/{stats['ok']}** ca OK. Tưới thực của phương án đứng đầu "
        f"(cùng mô hình FAO-56, thời tiết POWER thực): ENSO ít hơn ở {stats['better']} ca, nhiều hơn ở {stats['worse']} ca, "
        f"bằng ở {stats['ok'] - stats['better'] - stats['worse']} ca. Lưu ý top-1 là chiến lược `low_risk` (theo ưu tiên mặc định), "
        "không phải chiến lược tiết kiệm nước, nên tưới thực không phải thước đo duy nhất."
    )
    L.append(
        "- 2019: ONI ASO 2019 = +0,31 (trung tính) dù SON/OND sau đó lên El Niño yếu; quy tắc không nhìn trước "
        "nên engine KHÔNG gọi 2019–20 là năm El Niño. Năm 2018–19 là El Niño yếu (ASO +0,52) nhưng mùa khô mưa nhiều — ca trật điển hình."
    )
    L.append("\n## 4. Hạn chế\n")
    L.append(
        "- ONI là chỉ số NOAA (không phải NASA); NOAA hiệu chỉnh lại giá trị cũ (ERSST phiên bản mới), file bundled là bản 2026, "
        "nên giá trị quá khứ có thể khác chút so với bản công bố tại thời điểm đó.\n"
        "- Liên hệ thống kê với ~24 mùa khô; năm tương tự không phải dự báo, không có xác suất hiệu chỉnh.\n"
        "- Mưa IMERG/POWER là ô lưới (11 km / 50 km), không phải đo tại ruộng; không có quan trắc mặn nên không chấm được rủi ro mặn thật.\n"
        "- Thời điểm mặn của kịch bản năm tương tự giữ cửa sổ điển hình; ENSO không được dùng để dời mùa mặn.\n"
        "- Hindcast trước ~2012 có ít năm lịch sử (dữ liệu từ 2001), nên thường UNAVAILABLE.\n"
    )
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}; {stats}")


if __name__ == "__main__":
    main()
