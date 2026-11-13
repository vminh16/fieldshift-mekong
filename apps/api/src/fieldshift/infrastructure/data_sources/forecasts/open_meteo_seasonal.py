"""ECMWF SEAS5 via Open-Meteo (non-NASA, CC BY 4.0), cache-aside.

Use model metadata, never retrieval time, for issue_time. No archived forecasts are
used for hindcasts. Stale/malformed/unavailable data safely produce no forecast.
"""

import datetime as dt
import json
import math

import httpx

from fieldshift.infrastructure.data_sources import cache

URL = "https://seasonal-api.open-meteo.com/v1/seasonal"
META_URL = "https://seasonal-api.open-meteo.com/data/ecmwf_seas5/static/meta.json"
SOURCE = "Open-Meteo Seasonal / ECMWF SEAS5 (non-NASA)"
VARIABLES = {
    "temperature_2m_max": "tmax",
    "temperature_2m_min": "tmin",
    "precipitation_sum": "rain_mm",
}


def normalize(bundle: dict, as_of: dt.date) -> dict | None:
    try:
        meta = bundle["metadata"]
        issue = dt.datetime.fromtimestamp(meta["last_run_initialisation_time"], dt.timezone.utc)
        available = dt.datetime.fromtimestamp(meta["last_run_availability_time"], dt.timezone.utc)
        retrieved = dt.date.fromisoformat(bundle["retrieved_at"][:10])
        if not 0 <= (as_of - issue.date()).days <= 35 or max(available.date(), retrieved) > as_of:
            return None
        daily = bundle["payload"]["daily"]
        dates = [dt.date.fromisoformat(d) for d in daily["time"]]
        if len(set(dates)) != len(dates):
            return None
        # Unsuffixed variable is the control member, member01..50 are perturbed members.
        members = []
        omitted = []
        for key in daily:
            if key != "temperature_2m_max" and not key.startswith("temperature_2m_max_member"):
                continue
            suffix = key.removeprefix("temperature_2m_max")
            rows = {}
            for i, date in enumerate(dates):
                row = {target: daily[var + suffix][i] for var, target in VARIABLES.items()}
                if (
                    all(isinstance(v, (int, float)) and math.isfinite(v) for v in row.values())
                    and row["rain_mm"] >= 0
                    and row["tmin"] <= row["tmax"]
                ):
                    rows[str(date)] = row
            # Require an uninterrupted available forecast window, at least a month.
            end = min(dates[-1], as_of + dt.timedelta(days=179))
            if (end - as_of).days < 29 or not all(
                str(as_of + dt.timedelta(days=i)) in rows for i in range((end - as_of).days + 1)
            ):
                omitted.append(suffix.lstrip("_") or "control")
                continue
            members.append({"member_id": suffix.lstrip("_") or "control", "daily": rows})
        if not members:
            return None
        return {
            "issue_time": issue.isoformat(),
            "available_at": available.isoformat(),
            "source": SOURCE,
            "members": members,
            "omitted_member_ids": omitted,
            "quality_flags": [
                "SKILL_NOT_EVALUATED_MEKONG",
                "NOT_BIAS_CORRECTED",
                "ANALOG_FAO56_VARIABLES",
                "ANALOG_HORIZON_SPLICE",
            ]
            + (["INVALID_ENSEMBLE_MEMBERS_OMITTED"] if omitted else []),
        }
    except (KeyError, TypeError, ValueError, IndexError, OverflowError):
        return None


def load_seasonal(
    lat: float, lon: float, as_of: dt.date, cache_key: str | None = None
) -> tuple[dict | None, str]:
    if as_of < dt.date.today():
        return None, "HINDCAST_DISABLED"
    key = cache.key_for(lat, lon, cache_key)
    hit = cache.read("seasonal", key)
    forecast = normalize(hit, as_of) if hit else None
    if forecast:
        return forecast, "CACHED"
    try:
        meta_r = httpx.get(META_URL, timeout=15)
        meta_r.raise_for_status()
        r = httpx.get(
            URL,
            timeout=30,
            params={
                "latitude": lat,
                "longitude": lon,
                "models": "ecmwf_seas5",
                "daily": ",".join(VARIABLES),
                "forecast_days": 180,
            },
        )
        r.raise_for_status()
        check = httpx.get(META_URL, timeout=15)
        check.raise_for_status()
        if check.json() != meta_r.json():
            return None, "MODEL_UPDATE_IN_PROGRESS"
        bundle = {
            "metadata": meta_r.json(),
            "payload": r.json(),
            "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        forecast = normalize(bundle, as_of)
        if forecast:
            cache.write("seasonal", key, json.dumps(bundle))
            return forecast, "LIVE"
    except (httpx.HTTPError, ValueError):
        pass
    return None, "UNAVAILABLE_OR_STALE"
