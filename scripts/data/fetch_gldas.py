"""GLDAS Noah 2.1 monthly fallback: cloud OPeNDAP point windows after Data Rods closure.

AppEEARS catalog has no GLDAS. This fetches historical monthly means, NOT 3-hourly data.
"""

from __future__ import annotations

import calendar
import math
import re
import time
from urllib.parse import quote

import httpx
from common import DEFAULT_CACHE, SITES, get, write_json
from observations import EarthdataCurl, publish

VARS = {
    "SoilMoi0_10cm_inst": "kg m-2",
    "SoilMoi10_40cm_inst": "kg m-2",
    "Evap_tavg": "kg m-2 s-1",
    "Rainf_f_tavg": "kg m-2 s-1",
}
CACHE = DEFAULT_CACHE / "gldas"


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=90, transport=httpx.HTTPTransport(local_address="0.0.0.0")) as c:
        response = get(
            c,
            "https://cmr.earthdata.nasa.gov/search/granules.json",
            params={
                "short_name": "GLDAS_NOAH025_M",
                "version": "2.1",
                "page_size": 2000,
                "sort_key": "start_date",
                "temporal": "2001-01-01T00:00:00Z,2026-11-13T23:59:59Z",
            },
        )
        catalog = response.json()["feed"]["entry"]
        write_json(CACHE / "catalog.json", catalog)
    indices = {
        s: (math.floor((p["longitude"] + 180) * 4), math.floor((p["latitude"] + 60) * 4))
        for s, p in SITES.items()
    }
    xs = [x for x, y in indices.values()]
    ys = [y for x, y in indices.values()]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    ce = ",".join(f"{v}[0:1:0][{y0}:1:{y1}][{x0}:1:{x1}]" for v in VARS)
    curl = EarthdataCurl()
    tables = {s: [] for s in SITES}
    started = time.monotonic()

    def url(item):
        return next(link["href"] for link in item["links"] if "opendap" in link["href"])

    def checkpoint():
        for site, series in tables.items():
            x, y = indices[site]
            publish(
                "gldas",
                site,
                product="GLDAS_NOAH025_M",
                version="2.1",
                variables={
                    **{v: {"unit": u, "scale_applied": 1} for v, u in VARS.items()},
                    "soil_surface_m3_m3": {
                        "unit": "m3/m3",
                        "scale_applied": "SoilMoi0_10cm_inst / 100",
                    },
                    "soil_10_40cm_m3_m3": {
                        "unit": "m3/m3",
                        "scale_applied": "SoilMoi10_40cm_inst / 300",
                    },
                    "evap_mm_month": {
                        "unit": "mm/month",
                        "scale_applied": "Evap_tavg * seconds_in_month",
                    },
                    "rain_mm_month": {
                        "unit": "mm/month",
                        "scale_applied": "Rainf_f_tavg * seconds_in_month",
                    },
                },
                resolution="0.25 degree",
                cell={"longitude": -179.875 + x * 0.25, "latitude": -59.875 + y * 0.25},
                series=series,
                qa={
                    "note": "Data Rods discontinued; GLDAS absent from AppEEARS. Cloud OPeNDAP monthly fallback. Modeled monthly means; not current state. kg m-2 water equivalent / (1000 * depth_m) gives m3/m3. Evap can be negative (condensation).",
                    "coverage": "See .fieldshift/cache/gldas/progress.json",
                },
            )
        write_json(
            CACHE / "progress.json",
            {
                "completed": len(tables["cantho"]),
                "requested": len(catalog),
                "seconds": round(time.monotonic() - started, 2),
            },
        )

    try:
        dds = curl.get(url(catalog[0]) + ".dds")
        das = curl.get(url(catalog[0]) + ".das")
        (CACHE / "sample.dds").write_text(dds)
        (CACHE / "sample.das").write_text(das)
        for var, unit in VARS.items():
            if f"Float32 {var}[time = 1][lat = 600][lon = 1440]" not in dds:
                raise ValueError("GLDAS dimensions changed")
            block = re.search(r"\b" + var + r" \{(.*?)\}", das, re.S)[1]
            if f'"{unit}"' not in block:
                raise ValueError("GLDAS units changed: " + var)
        for n, item in enumerate(catalog, 1):
            day = item["time_start"][:10]
            path = CACHE / "raw" / (day + ".ascii")
            path.parent.mkdir(exist_ok=True)
            text = (
                path.read_text()
                if path.exists()
                else curl.get(url(item) + ".ascii?" + quote(ce, safe=",:."))
            )
            values = {}
            for v in VARS:
                matches = re.findall(r"(?m)^" + v + r"\." + v + r"\[[^\n]+?\],\s*([^\n]+)", text)
                if not matches:
                    matches = re.findall(
                        r"(?m)^" + v + r"(?:\." + v + r")?\[0\]\[\d+\],\s*([^\n]+)", text
                    )
                rows = [[float(a.strip()) for a in line.split(",")] for line in matches]
                if len(rows) != y1 - y0 + 1 or any(len(r) != x1 - x0 + 1 for r in rows):
                    (CACHE / "unexpected.ascii").write_text(text)
                    raise ValueError("Unexpected GLDAS ASCII format")
                values[v] = {s: rows[y - y0][x - x0] for s, (x, y) in indices.items()}
            path.write_text(text)
            seconds = 86400 * calendar.monthrange(int(day[:4]), int(day[5:7]))[1]
            for s in SITES:
                row = {
                    "date": day,
                    **{
                        v: (
                            values[v][s]
                            if math.isfinite(values[v][s]) and values[v][s] > -9990
                            else None
                        )
                        for v in VARS
                    },
                }
                for output, var, scale in [
                    ("soil_surface_m3_m3", "SoilMoi0_10cm_inst", 0.01),
                    ("soil_10_40cm_m3_m3", "SoilMoi10_40cm_inst", 1 / 300),
                    ("evap_mm_month", "Evap_tavg", seconds),
                    ("rain_mm_month", "Rainf_f_tavg", seconds),
                ]:
                    row[output] = round(row[var] * scale, 7) if row[var] is not None else None
                tables[s].append(row)
            if n % 10 == 0 or n == 1 or n == len(catalog):
                checkpoint()
                print(n, len(catalog), day, round(time.monotonic() - started, 1), flush=True)
    finally:
        if tables["cantho"]:
            checkpoint()
        curl.close()


if __name__ == "__main__":
    main()
