import copy
import datetime as dt

import httpx
import pytest

from fieldshift.domain.engines.future_outlook import build_weather
from fieldshift.infrastructure.data_sources import cache, glofas
from fieldshift.infrastructure.data_sources.forecasts import open_meteo_seasonal as seasonal
from fieldshift.infrastructure.data_sources.nasa.nex_cmip6 import load_projections

AS_OF = dt.date(2026, 11, 14)


@pytest.mark.parametrize("site", ["cantho", "chaudoc", "bentre", "soctrang"])
def test_bundled_ensemble(site):
    f = seasonal.normalize(cache.read("seasonal", site), AS_OF)
    assert 1 < len(f["members"]) <= 51
    assert len(f["members"]) + len(f["omitted_member_ids"]) == 51
    assert "INVALID_ENSEMBLE_MEMBERS_OMITTED" in f["quality_flags"]
    assert len({m["member_id"] for m in f["members"]}) == len(f["members"])
    assert f["issue_time"].startswith("2026-11-01")
    assert all(m["daily"][str(AS_OF)]["rain_mm"] >= 0 for m in f["members"])


def test_forecast_freshness_hindcast_and_missing(monkeypatch):
    bundle = cache.read("seasonal", "cantho")
    assert seasonal.normalize(bundle, dt.date(2026, 10, 31)) is None
    assert seasonal.normalize(bundle, dt.date(2026, 12, 7)) is None
    assert seasonal.load_seasonal(10.03, 105.78, dt.date(2026, 11, 12), "cantho") == (
        None,
        "HINDCAST_DISABLED",
    )
    broken = copy.deepcopy(bundle)
    broken["payload"]["daily"]["precipitation_sum"] = []
    assert seasonal.normalize(broken, AS_OF) is None
    monkeypatch.setattr(cache, "read", lambda *args: None)
    assert seasonal.load_seasonal(10, 105, AS_OF)[0] is None


def test_live_cache_aside(monkeypatch):
    bundle = cache.read("seasonal", "cantho")
    monkeypatch.setattr(cache, "read", lambda *args: None)
    writes = []
    monkeypatch.setattr(cache, "write", lambda *args: writes.append(args))

    def get(url, **kwargs):
        payload = bundle["metadata"] if url == seasonal.META_URL else bundle["payload"]
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", get)
    assert seasonal.load_seasonal(10, 105, AS_OF)[1] == "LIVE"
    assert writes[0][0] == "seasonal"


def test_projection_delta_and_splice():
    projections, notes = load_projections("cantho")
    assert len(projections) == 4 and not notes
    assert load_projections("soctrang")[0] == []
    assert load_projections("soctrang")[1]
    day = {
        "date": dt.date(2024, 1, 1),
        "tmax": 30,
        "tmin": 20,
        "tdew": 19,
        "rain_mm": 4,
        "rs_mj": 20,
        "u2": 2,
    }
    ctx = {"weather": [{**day, "date": day["date"] + dt.timedelta(days=i)} for i in range(190)]}
    forecast = {
        str(dt.date(2026, 1, 1) + dt.timedelta(days=i)): {"tmax": 33, "tmin": 21, "rain_mm": 8}
        for i in range(181)
    }
    weather = build_weather(ctx, dt.date(2026, 1, 1), 185, 2024, forecast_daily=forecast)
    assert weather[0]["tmax"] == 33
    assert weather[0]["tdew"] == 19 and weather[0]["rs_mj"] == 20
    assert weather[180]["tmax"] == 30  # forecast ends at 180 days
    monthly = build_weather(
        ctx,
        dt.date(2026, 1, 1),
        0,
        2024,
        monthly_tmax_delta={"1": 2},
        monthly_rain_factor={"1": 0.5},
    )[0]
    assert monthly["tmax"] == 32 and monthly["rain_mm"] == 2 and monthly["tmin"] == 20


def test_discharge_signal_real_and_missing():
    current = cache.read("glofas", "tan_chau")
    history = cache.read("glofas", "tan_chau_history")
    s = glofas.signal(current, history, AS_OF)
    assert s["value"] > 0 and s["date"] <= str(AS_OF)
    assert s["climatology_years"] == 20
    assert s["anomaly_pct"] < 0
    assert glofas.signal(current, None, AS_OF)["anomaly_pct"] is None
    assert glofas.signal(current, history, dt.date(2026, 11, 1))["value"] is None
    assert glofas.signal(current, history, dt.date(2026, 12, 1))["value"] is None
    assert glofas.load_discharge(dt.date(2026, 11, 1))[1] == "HINDCAST_DISABLED"
