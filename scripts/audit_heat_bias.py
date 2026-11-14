"""Reproduce A7 before/after with only the heat policy changed (offline demo bundles)."""

import datetime as dt
import gzip
import json
import statistics as st
from pathlib import Path

import sensitivity
from fastapi.testclient import TestClient
from fieldshift.application.use_cases.plan_rotation import context_for
from fieldshift.domain.engines.field_state import estimate_state
from fieldshift.domain.engines.rotation_planner import run_plan
from fieldshift.infrastructure.crop_models.fao56_water import simulate_season
from fieldshift.infrastructure.data_sources.heat_conflict import RESOURCES
from fieldshift.infrastructure.persistence import sqlite as db
from fieldshift.main import app

AS_OF = dt.date(2026, 11, 14)
OUT = Path(__file__).resolve().parents[1] / "docs/HEAT_BIAS_REPORT.md"


def main():
    sensitivity.go_offline()
    lines = [
        "# A7 — xung đột Tmax POWER / ERA5\n",
        "Sinh bởi `scripts/audit_heat_bias.py`, offline, as_of 14/11/2026. Mỗi phép so chỉ tắt/bật hiệu chỉnh ngày nóng, giữ cùng khung mặn và mọi đầu vào khác.\n",
        "Chính sách §7.3: dùng các cặp ngày trước as_of để tính chênh lệch trung bình theo tháng (ít nhất 60 ngày). Khi |POWER − ERA5| > 2 °C, trừ chênh lệch khỏi Tmax **chỉ để đếm ngày nóng**. Còn lại dùng POWER gốc. Giữ cả hai nguồn và `source_conflicts`; không phải đo tại thửa hay kiểm định cực trị ngày. Ngoài 4 bundle ERA5, giữ POWER và ghi UNAVAILABLE.\n",
        "ET₀ giữ nguyên Tmax/Tmin/điểm sương/bức xạ/gió POWER để không ghép một vector khí tượng chưa hiệu chỉnh đồng bộ. Vì vậy không tuyên bố đã sửa sai lệch ET₀; tưới tuyệt đối vẫn là ước tính mô hình. Các số tưới dưới đây là baseline cố định, chưa lẫn tác động đổi lựa chọn.\n",
        "## Tháng 3, 2001–2025\n",
        "| Ruộng | Tmax POWER / ERA5 (°C) | Ngày ≥35 °C/năm POWER / sau chỉnh / ERA5 |",
        "|---|---|---|",
    ]
    impacts, picks = [], []
    with TestClient(app):
        for site, label in [
            ("cantho", "Cần Thơ"),
            ("chaudoc", "Châu Đốc"),
            ("bentre", "Bến Tre"),
            ("soctrang", "Sóc Trăng"),
        ]:
            f = db.get(db.connect(), "fields", "fld_" + site)
            ctx = context_for(f, AS_OF)
            raw_ctx = {
                **ctx,
                "weather": [
                    {k: v for k, v in w.items() if k != "heat_tmax"} for w in ctx["weather"]
                ],
            }
            state = estimate_state(f, ctx, AS_OF, [])
            req = {"as_of": str(AS_OF), "horizon_seasons": 3}
            before, after = [
                run_plan(f, c, state, req, simulate=simulate_season) for c in (raw_ctx, ctx)
            ]
            raw = [
                w for w in ctx["weather"] if 2001 <= w["date"].year <= 2025 and w["date"].month == 3
            ]
            era = [
                r["temperature_2m_max"]
                for r in json.loads(gzip.decompress((RESOURCES / f"{site}.json.gz").read_bytes()))[
                    "series"
                ]
                if r["date"][:4] <= "2025"
                and r["date"][5:7] == "03"
                and r.get("temperature_2m_max") is not None
            ]
            lines.append(
                f"| {label} | {st.mean(w['tmax'] for w in raw):.1f} / {st.mean(era):.1f} | {sum(w['tmax'] >= 35 for w in raw) / 25:.1f} / {sum(w['heat_tmax'] >= 35 for w in raw) / 25:.1f} / {sum(t >= 35 for t in era) / 25:.1f} |"
            )

            def metric(p, key):
                return p["baseline"]["metrics"]["sc_clim"][key]["value"]

            def rules(p):
                return sum(r["rule_id"] == "R_HEAT" for r in p["baseline"]["rules"])

            assert before["baseline"]["sequence_id"] == after["baseline"]["sequence_id"]
            assert metric(before, "irrigation_need") == metric(after, "irrigation_need")
            top_before = before["options"][0]["metrics"]["sc_clim"]["irrigation_need"]["value"]
            top_after = after["options"][0]["metrics"]["sc_clim"]["irrigation_need"]["value"]
            impacts.append(
                f"| {label} | {metric(before, 'heat_stress_days_sensitive_stage')} → {metric(after, 'heat_stress_days_sensitive_stage')} | {rules(before)} → {rules(after)} | {metric(before, 'irrigation_need')} → {metric(after, 'irrigation_need')} | 0 | {top_before} → {top_after} |"
            )
            picks.append(
                f"- {label}: top-1 trước `{before['options'][0]['sequence_id']}`, sau `{after['options'][0]['sequence_id']}`; shortlist sau: "
                + ", ".join(
                    f"`{o['strategy_tag']}: {'/'.join(s['crop'] for s in o['seasons'])}`"
                    for o in after["options"]
                )
            )
            print(label, impacts[-1], flush=True)
    lines += [
        "\n## 3 vụ tới: baseline lúa cố định, sc_clim (trung vị)\n",
        "| Ruộng | Ngày nóng giai đoạn nhạy cảm trước → sau | Số cờ R_HEAT trước → sau | Tưới (mm) trước → sau | Δ ET₀ / tưới do chỉnh nhiệt (mm) | Tưới top-1 trước → sau (mm, có thể đổi chuỗi) |",
        "|---|---|---|---|---|---|",
        *impacts,
        "\n## Lựa chọn sau A7\n",
        *picks,
        "\nCần Thơ/Châu Đốc giảm rõ ngày nóng khi đối chiếu ERA5; Sóc Trăng không tự tăng nóng để bù ô biển. Ngưỡng xung đột và hiệu chỉnh trung bình tháng là giả định nhóm, cần kiểm định độc lập. Việc chọn chuỗi có thể đổi vì R_HEAT/stress đổi; không gọi đó là giảm nước do hiệu chỉnh ET₀.",
    ]
    OUT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
