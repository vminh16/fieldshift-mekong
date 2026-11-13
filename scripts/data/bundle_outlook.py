"""Refresh bundled Open-Meteo demo responses (manual, network required; CC BY 4.0)."""

import datetime as dt
import gzip
import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
RESOURCES = ROOT / "apps/api/src/fieldshift/resources"
SEASONAL = "https://seasonal-api.open-meteo.com"
FLOOD = "https://flood-api.open-meteo.com/v1/flood"
META = SEASONAL + "/data/ecmwf_seas5/static/meta.json"


def save(source, key, payload):
    path = RESOURCES / "demo_cache" / source / f"{key}.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(payload).encode(), mtime=0))
    print(path.relative_to(ROOT), path.stat().st_size, flush=True)


def get(client, url, **params):
    r = client.get(url, params=params)
    r.raise_for_status()
    return r.json()


def main():
    with httpx.Client(timeout=60) as client:
        metadata = get(client, META)
        fields = json.loads((RESOURCES / "regions.json").read_text())["regions"][0]["demo_fields"]
        for field in fields:
            data = get(
                client,
                SEASONAL + "/v1/seasonal",
                latitude=field["lat"],
                longitude=field["lon"],
                models="ecmwf_seas5",
                daily="temperature_2m_max,temperature_2m_min,precipitation_sum",
                forecast_days=180,
            )
            if get(client, META) != metadata:
                raise RuntimeError("Model updated during capture; retry")
            save(
                "seasonal",
                field["cache_key"],
                {
                    "metadata": metadata,
                    "payload": data,
                    "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "request": {
                        "latitude": field["lat"],
                        "longitude": field["lon"],
                        "models": "ecmwf_seas5",
                    },
                },
            )
        for key, params in [
            ("tan_chau", {"past_days": 30, "forecast_days": 7}),
            ("tan_chau_history", {"start_date": "2001-01-01", "end_date": "2020-12-31"}),
        ]:
            save(
                "glofas",
                key,
                {
                    "payload": get(
                        client,
                        FLOOD,
                        latitude=10.80,
                        longitude=105.24,
                        daily="river_discharge",
                        **params,
                    ),
                    "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "request": params,
                },
            )


if __name__ == "__main__":
    main()
