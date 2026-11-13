"""NASA POWER Daily point adapter (no auth). Cache-first; offline falls back to nearest cached cell."""

import datetime as dt

import httpx

from fieldshift.infrastructure.data_sources import cache

POWER_PARAMS = (
    "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M,ALLSKY_SFC_SW_DWN,EVPTRNS,"
    "GWETROOT,GWETTOP,GWETPROF,T2MDEW"
)
POWER_START = "20010101"
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


class PowerUnavailable(RuntimeError):
    pass


def load_power(lat: float, lon: float, cache_key: str | None = None) -> tuple[dict, str]:
    """Returns (payload, status LIVE|CACHED|CACHED_NEARBY_CELL)."""
    key = cache.key_for(lat, lon, cache_key)
    hit = cache.read("power", key)
    if hit is not None:
        return hit, "CACHED"
    end = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y%m%d")
    try:
        r = httpx.get(
            URL,
            timeout=120,
            params={
                "parameters": POWER_PARAMS,
                "community": "AG",
                "longitude": lon,
                "latitude": lat,
                "start": POWER_START,
                "end": end,
                "format": "JSON",
            },
        )
        r.raise_for_status()
    except httpx.HTTPError:
        return _nearest(lat, lon)  # UC-09: degrade, never invent
    cache.write("power", key, r.text)
    return r.json(), "LIVE"


def _nearest(lat: float, lon: float, max_deg: float = 0.5) -> tuple[dict, str]:
    """Nearest cached POWER cell within max_deg (~1 POWER cell). ponytail: linear scan of cache."""
    best = None
    for payload in cache.all_entries("power"):
        clon, clat = payload["geometry"]["coordinates"][:2]
        d = max(abs(clat - lat), abs(clon - lon))
        if d <= max_deg and (best is None or d < best[0]):
            best = (d, payload)
    if best is None:
        raise PowerUnavailable(
            "NASA POWER không truy cập được và không có cache gần (≤0.5°) cho vị trí này"
        )
    return best[1], "CACHED_NEARBY_CELL"
