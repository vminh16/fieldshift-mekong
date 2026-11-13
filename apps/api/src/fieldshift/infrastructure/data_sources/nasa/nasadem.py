"""Terrain adapter: SRTM 30 m via OpenTopoData (no auth). Failure degrades to UNAVAILABLE."""

import json

import httpx

from fieldshift.infrastructure.data_sources import cache


def load_elevation(
    lat: float, lon: float, cache_key: str | None = None
) -> tuple[float | None, str]:
    key = cache.key_for(lat, lon, cache_key)
    hit = cache.read("srtm", key)
    if hit is not None:
        return hit["elevation"], "CACHED"
    try:
        r = httpx.get(f"https://api.opentopodata.org/v1/srtm30m?locations={lat},{lon}", timeout=15)
        elev = r.json()["results"][0]["elevation"]
    except Exception:  # offline/rate-limited: degrade, don't fail the plan
        return None, "UNAVAILABLE"
    cache.write("srtm", key, json.dumps({"elevation": elev, "source": "OpenTopoData srtm30m"}))
    return elev, "LIVE"
