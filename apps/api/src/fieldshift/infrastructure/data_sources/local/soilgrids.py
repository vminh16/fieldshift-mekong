"""ISRIC SoilGrids v2.0 topsoil adapter; on failure returns the regional prior labelled ASSUMPTION."""

import json

import httpx

from fieldshift.infrastructure.data_sources import cache


def load_soil(
    lat: float, lon: float, region: dict, cache_key: str | None = None
) -> tuple[dict, str]:
    key = cache.key_for(lat, lon, cache_key)
    hit = cache.read("soilgrids", key)
    if hit is not None:
        return hit, "CACHED"
    try:
        r = httpx.get(
            "https://rest.isric.org/soilgrids/v2.0/properties/query",
            timeout=8,
            params=[
                ("lon", lon),
                ("lat", lat),
                ("property", "clay"),
                ("property", "sand"),
                ("property", "phh2o"),
                ("property", "soc"),
                ("depth", "0-5cm"),
                ("depth", "15-30cm"),
                ("value", "mean"),
            ],
        )
        r.raise_for_status()
        out = {}
        for layer in r.json()["properties"]["layers"]:
            d = layer["unit_measure"]["d_factor"]
            out[layer["name"]] = {
                x["label"]: (x["values"]["mean"] / d if x["values"]["mean"] is not None else None)
                for x in layer["depths"]
            }
        soil = {"source": "SoilGrids v2.0", "kind": "OBSERVED_REMOTE_ESTIMATE", "properties": out}
    except Exception:
        prior = {"source": "region_prior", "kind": "ASSUMPTION", "properties": region["soil_prior"]}
        return prior, "UNAVAILABLE"
    cache.write("soilgrids", key, json.dumps(soil))
    return soil, "LIVE"
