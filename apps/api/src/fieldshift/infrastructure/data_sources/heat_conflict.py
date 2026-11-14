"""Explicit §7.3 precedence: correct heat counts only; retain POWER for FAO-56.

Monthly paired means use dates strictly before as_of. This reduces a documented warm
bias; it is not a calibrated daily extreme-temperature product or a field measurement.
"""

import datetime as dt
import gzip
import json
import statistics as st
from pathlib import Path

HEAT_CONFLICT_THRESHOLD_C = 2.0
MIN_PAIRED_DAYS_PER_MONTH = 60
RESOURCES = Path(__file__).resolve().parents[2] / "resources/observations/era5_openmeteo"
HEAT_EVIDENCE = ["ev_power_daily", "ev_era5", "ev_heat_conflict"]


def apply_heat_policy(weather: list[dict], cache_key: str | None, as_of: dt.date) -> dict:
    path = RESOURCES / f"{cache_key}.json.gz"
    if not cache_key or not path.exists():
        return {
            "status": "UNAVAILABLE",
            "policy": "POWER_RAW_NO_ERA5_BUNDLE",
            "evidence_ids": ["ev_power_daily"],
        }
    data = json.loads(gzip.decompress(path.read_bytes()))
    era = {
        dt.date.fromisoformat(r["date"]): r["temperature_2m_max"]
        for r in data["series"]
        if r.get("temperature_2m_max") is not None and dt.date.fromisoformat(r["date"]) < as_of
    }
    pairs = {m: [] for m in range(1, 13)}
    for w in weather:
        if w["date"] < as_of and w["date"] in era and w.get("tmax") is not None:
            pairs[w["date"].month].append((w["tmax"], era[w["date"]]))
    months = {}
    for m, rows in pairs.items():
        if len(rows) < MIN_PAIRED_DAYS_PER_MONTH:
            continue
        bias = st.mean(p - e for p, e in rows)
        correction = bias if abs(bias) > HEAT_CONFLICT_THRESHOLD_C else 0.0
        months[str(m)] = {
            "paired_days": len(rows),
            "power_mean_c": round(st.mean(p for p, _ in rows), 3),
            "era5_mean_c": round(st.mean(e for _, e in rows), 3),
            "power_minus_era5_c": round(bias, 3),
            "heat_correction_c": correction,
        }
    if not months:
        return {
            "status": "UNAVAILABLE",
            "policy": "POWER_RAW_INSUFFICIENT_ERA5_PAIRS",
            "note_vi": "Chưa đủ 60 cặp ngày trong một tháng trước as_of để đối chiếu; giữ Tmax POWER thô.",
            "evidence_ids": ["ev_power_daily"],
        }
    for w in weather:
        # Never replace tmax: ET0 must receive the original coherent POWER input vector.
        w["heat_tmax"] = w["tmax"] - months.get(str(w["date"].month), {}).get(
            "heat_correction_c", 0
        )
    return {
        "status": "APPLIED",
        "policy": "MONTHLY_MEAN_BIAS_CORRECTION_HEAT_ONLY",
        "threshold_c": HEAT_CONFLICT_THRESHOLD_C,
        "months": months,
        "fit_before": str(as_of),
        "et0_uses": "ORIGINAL_POWER_TMAX",
        "note_vi": "Đếm ngày nóng bằng Tmax POWER đã chỉnh chênh lệch trung bình tháng với ERA5 khi |chênh lệch| > 2 °C. Giữ cả hai nguồn; chưa kiểm định cực trị ngày. ET₀ và tưới giữ nguyên đầu vào POWER; sai lệch nhu cầu tưới tuyệt đối vẫn còn.",
        "evidence_ids": HEAT_EVIDENCE,
    }
