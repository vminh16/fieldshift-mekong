"""Fetch consistent ERA5 daily point series via Open-Meteo, with POWER comparisons."""

from __future__ import annotations

import json
import time
from datetime import date, timedelta

import httpx
from common import DEFAULT_CACHE, SITES, get, write_json
from observations import power_et0, power_values, publish, stats

VARIABLES = {
    "temperature_2m_max": "°C",
    "temperature_2m_min": "°C",
    "precipitation_sum": "mm",
    "et0_fao_evapotranspiration": "mm",
}


def main():
    directory = DEFAULT_CACHE / "era5_openmeteo"
    # ERA5T is normally available after five days. Avoid silently mixing IFS/ERA5-Land.
    end = (date.today() - timedelta(days=5)).isoformat()
    with httpx.Client(
        timeout=180, transport=httpx.HTTPTransport(local_address="0.0.0.0")
    ) as client:
        for site, point in SITES.items():
            path = directory / (site + ".json")
            if path.exists():
                data = json.loads(path.read_text())
            else:
                params = {
                    "latitude": point["latitude"],
                    "longitude": point["longitude"],
                    "start_date": "2001-01-01",
                    "end_date": end,
                    "models": "era5",
                    "daily": ",".join(VARIABLES),
                    "timezone": "UTC",
                    "elevation": "nan",
                    "cell_selection": "nearest",
                }
                while True:
                    try:
                        response = get(
                            client, "https://archive-api.open-meteo.com/v1/archive", params=params
                        )
                        break
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code != 429:
                            raise
                        print(site, "rate limited; retry in 65 seconds", flush=True)
                        time.sleep(65)
                data = response.json()
                write_json(path, data)
                write_json(directory / (site + "_request.json"), {"url": str(response.url)})
            for name, unit in VARIABLES.items():
                if data["daily_units"][name] != unit:
                    raise ValueError("Unexpected ERA5 units: " + name)
            series = [
                {"date": d, **{v: data["daily"][v][i] for v in VARIABLES}}
                for i, d in enumerate(data["daily"]["time"])
            ]
            if len({r["date"] for r in series}) != len(series):
                raise ValueError("Duplicate dates")
            comparisons = {}
            for variable, power_name in [
                ("temperature_2m_max", "T2M_MAX"),
                ("temperature_2m_min", "T2M_MIN"),
                ("precipitation_sum", "PRECTOTCORR"),
            ]:
                ref = power_values(site, power_name)
                comparisons[variable] = stats([(r[variable], ref.get(r["date"])) for r in series])
            ref_et0 = power_et0(site)
            comparisons["et0_fao_evapotranspiration"] = stats(
                [(r["et0_fao_evapotranspiration"], ref_et0.get(r["date"])) for r in series]
            )
            publish(
                "era5_openmeteo",
                site,
                product="ERA5 via Open-Meteo archive",
                version="ERA5/ERA5T",
                variables={
                    v: {"unit": "degC" if u == "°C" else "mm/day", "scale_applied": 1}
                    for v, u in VARIABLES.items()
                },
                resolution="0.25 degree",
                cell={"latitude": data["latitude"], "longitude": data["longitude"]},
                series=series,
                qa={
                    "POWER_daily": comparisons,
                    "missing_values": {v: sum(r[v] is None for r in series) for v in VARIABLES},
                    "note": "UTC daily; no elevation downscaling; ET0 is FAO reference ET, not actual ET. Recent ERA5T preliminary. POWER ET0 comparator: project FAO-56 Penman-Monteith from POWER weather, requested latitude and bundled SRTM elevation; missing inputs excluded.",
                },
                license="CC BY 4.0 Open-Meteo; Copernicus ERA5 attribution",
                source_url="https://open-meteo.com/en/docs/historical-weather-api",
            )
            print(site, len(series), series[0]["date"], series[-1]["date"], comparisons, flush=True)
            time.sleep(2)


if __name__ == "__main__":
    main()
