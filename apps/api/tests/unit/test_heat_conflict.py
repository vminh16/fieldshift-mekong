import datetime as dt
import gzip
import json

import pytest

from fieldshift.domain.catalog import CROP_BY_ID
from fieldshift.domain.engines.future_outlook import build_weather
from fieldshift.infrastructure.crop_models.fao56_water import simulate_season
from fieldshift.infrastructure.data_sources import heat_conflict as hc


def test_heat_policy_preserves_power_and_ignores_future_in_fit(tmp_path, monkeypatch):
    monkeypatch.setattr(hc, "RESOURCES", tmp_path)
    rows = [
        {"date": f"{year}-03-{day:02d}", "temperature_2m_max": 32.0}
        for year in (2023, 2024, 2025)
        for day in range(1, 29)
    ]
    rows.append({"date": "2027-03-01", "temperature_2m_max": -20})
    (tmp_path / "test.json.gz").write_bytes(gzip.compress(json.dumps({"series": rows}).encode()))
    weather = [{"date": dt.date.fromisoformat(r["date"]), "tmax": 36.0} for r in rows]
    report = hc.apply_heat_policy(weather, "test", dt.date(2026, 1, 1))
    assert report["months"]["3"]["heat_correction_c"] == 4
    assert report["months"]["3"]["paired_days"] == 84
    assert all(w["tmax"] == 36 and w["heat_tmax"] == 32 for w in weather)
    assert set(report["evidence_ids"]) == {"ev_power_daily", "ev_era5", "ev_heat_conflict"}
    assert hc.apply_heat_policy(weather, None, dt.date(2026, 1, 1))["status"] == "UNAVAILABLE"


def test_heat_count_correction_does_not_change_water_balance():
    start = dt.date(2025, 1, 1)
    raw = [
        {
            "date": start + dt.timedelta(days=i),
            "tmax": 36,
            "tmin": 24,
            "tdew": 23,
            "rs_mj": 18,
            "u2": 2,
            "rain_mm": 0,
        }
        for i in range(120)
    ]
    corrected = [{**w, "heat_tmax": 32} for w in raw]
    from fieldshift.domain.catalog import REGIONS

    args = (CROP_BY_ID["rice"], start, 10, 2, REGIONS["mekong"]["paddy"], {"taw_mm_per_m": 150})
    a, b = (simulate_season(w, *args) for w in (raw, corrected))
    assert a["heat_stress_days_sensitive"] > b["heat_stress_days_sensitive"] == 0
    for key in ("et0_mm", "irrigation_mm", "water_stress_days", "end_state"):
        assert a[key] == b[key]


def test_heat_policy_follows_temperature_scenarios_and_seas5():
    h = {
        "date": dt.date(2025, 3, 1),
        "tmax": 36,
        "heat_tmax": 32,
        "tmin": 24,
        "tdew": 22,
        "rain_mm": 1,
    }
    ctx = {"weather": [h]}
    out = build_weather(
        ctx, dt.date(2026, 3, 1), 0, 2025, temp_delta=1.5, monthly_tmax_delta={"3": 1}
    )
    assert out[0]["tmax"] == 38.5 and out[0]["heat_tmax"] == 34.5
    out = build_weather(
        ctx, dt.date(2026, 3, 1), 0, 2025, forecast_daily={"2026-03-01": {"tmax": 34}}
    )
    assert out[0]["heat_tmax"] == 34


@pytest.mark.parametrize("bias,expected", [(1.5, 0), (2, 0), (2.1, 2.1), (-3, -3)])
def test_monthly_conflict_threshold(tmp_path, monkeypatch, bias, expected):
    monkeypatch.setattr(hc, "RESOURCES", tmp_path)
    dates = [dt.date(y, 3, d) for y in (2023, 2024, 2025) for d in range(1, 29)]
    data = {"series": [{"date": str(d), "temperature_2m_max": 32} for d in dates]}
    (tmp_path / "test.json.gz").write_bytes(gzip.compress(json.dumps(data).encode()))
    out = hc.apply_heat_policy(
        [{"date": d, "tmax": 32 + bias} for d in dates], "test", dt.date(2026, 1, 1)
    )
    assert out["months"]["3"]["heat_correction_c"] == pytest.approx(expected)


def test_insufficient_monthly_pairs_stays_raw(tmp_path, monkeypatch):
    monkeypatch.setattr(hc, "RESOURCES", tmp_path)
    (tmp_path / "test.json.gz").write_bytes(
        gzip.compress(
            json.dumps({"series": [{"date": "2025-03-01", "temperature_2m_max": 32}]}).encode()
        )
    )
    weather = [{"date": dt.date(2025, 3, 1), "tmax": 36}]
    result = hc.apply_heat_policy(weather, "test", dt.date(2026, 1, 1))
    assert result["status"] == "UNAVAILABLE"
    assert weather == [{"date": dt.date(2025, 3, 1), "tmax": 36}]
