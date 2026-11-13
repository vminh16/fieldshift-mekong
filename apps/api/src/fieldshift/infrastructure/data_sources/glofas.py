"""Regional upstream discharge context, never a canal salinity measurement.

Open-Meteo/GloFAS at Tân Châu (10.80, 105.24). Anomaly compares trailing
7-day means with the same calendar window in each available historical year.
"""

import datetime as dt
import json
import math
import statistics as st

import httpx

from fieldshift.domain.engines.future_outlook import shift_year
from fieldshift.infrastructure.data_sources import cache

URL = "https://flood-api.open-meteo.com/v1/flood"
PARAMS = {"latitude": 10.80, "longitude": 105.24, "daily": "river_discharge"}


def rows(bundle):
    daily = bundle["payload"]["daily"]
    return {
        dt.date.fromisoformat(d): v
        for d, v in zip(daily["time"], daily["river_discharge"], strict=True)
        if isinstance(v, (int, float)) and math.isfinite(v) and v >= 0
    }


def signal(current: dict | None, history: dict | None, as_of: dt.date) -> dict:
    empty = {
        "value": None,
        "anomaly_pct": None,
        "trend_m3_s_per_day": None,
        "reason": "GLOFAS_UNAVAILABLE_OR_STALE",
    }
    try:
        if current is None or dt.date.fromisoformat(current["retrieved_at"][:10]) > as_of:
            return empty
        available = dt.date.fromisoformat(current["retrieved_at"][:10])
        recent = {d: v for d, v in rows(current).items() if d <= min(as_of, available)}
        end = max(recent)
        if (as_of - end).days > 7:
            return empty
        dates = [end - dt.timedelta(days=i) for i in range(7)]
        values = [recent[d] for d in dates if d in recent]
        result = {
            **empty,
            "value": recent[end],
            "date": str(end),
            "reason": None,
            "trend_m3_s_per_day": (recent[end] - recent[dates[-1]]) / 6
            if dates[-1] in recent
            else None,
        }
        if history and len(values) == 7 and history["retrieved_at"][:10] <= str(as_of):
            hist = rows(history)
            means = []
            for year in sorted({d.year for d in hist if d.year < end.year}):
                window = [shift_year(d, year - end.year) for d in dates]
                if all(d in hist for d in window):
                    means.append(st.mean(hist[d] for d in window))
            if means and st.mean(means) > 0:
                result.update(
                    anomaly_pct=round(100 * (st.mean(values) / st.mean(means) - 1), 1),
                    climatology_years=len(means),
                )
        return result
    except (KeyError, TypeError, ValueError):
        return empty


def _load(key, params, refresh=False):
    hit = cache.read("glofas", key)
    if hit and (not refresh or hit["retrieved_at"][:10] >= str(dt.date.today())):
        return hit, "CACHED"
    try:
        r = httpx.get(URL, params={**PARAMS, **params}, timeout=30)
        r.raise_for_status()
        bundle = {
            "payload": r.json(),
            "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "request": params,
        }
        rows(bundle)  # validate before caching
        cache.write("glofas", key, json.dumps(bundle))
        return bundle, "LIVE"
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        return hit, "CACHED" if hit else "UNAVAILABLE"


def load_discharge(as_of: dt.date) -> tuple[dict, str]:
    if as_of < dt.date.today():
        return signal(None, None, as_of), "HINDCAST_DISABLED"
    current, status = _load("tan_chau", {"past_days": 30, "forecast_days": 7}, refresh=True)
    history, _ = _load("tan_chau_history", {"start_date": "2001-01-01", "end_date": "2020-12-31"})
    result = signal(current, history, as_of)
    return result, status if result["value"] is not None else "UNAVAILABLE_OR_STALE"
