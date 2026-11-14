#!/usr/bin/env python3
"""NEX v2 point CSV via public NCCS NCSS; discover exact objects/sizes on AWS.

uv run --no-project --with httpx python scripts/data/fetch_nex_cmip6.py --sites cantho
No auth. NCSS subsets the same NASA collection on the server. AWS global files
are NOT downloaded. --plan lists the exact AWS keys/bytes without extraction.
"""

from __future__ import annotations

import argparse
import calendar
import concurrent.futures
import csv
import io
import math
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode

import httpx
from common import DEFAULT_CACHE, ROOT, SITES, envelope, get, write_json

BUCKET = "https://nex-gddp-cmip6.s3.amazonaws.com/"
NCSS = "https://ds.nccs.nasa.gov/thredds/ncss/grid/AMES/NEX/GDDP-CMIP6/"
NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}


def discover(client, model, scenario, variable, start, end):
    prefix = f"NEX-GDDP-CMIP6/{model}/{scenario}/r1i1p1f1/{variable}/"
    objects, token = {}, None
    while True:
        params = {"list-type": "2", "prefix": prefix, "max-keys": 1000}
        if token:
            params["continuation-token"] = token
        root = ET.fromstring(get(client, BUCKET, params=params).content)
        for node in root.findall("s:Contents", NS):
            key = node.findtext("s:Key", namespaces=NS)
            objects[key] = int(node.findtext("s:Size", namespaces=NS))
        token = root.findtext("s:NextContinuationToken", namespaces=NS)
        if not token:
            break
    result = []
    for year in range(start, end + 1):
        # Pin v2: never silently mix a retracted/old v1 series into v2.
        key = prefix + f"{variable}_day_{model}_{scenario}_r1i1p1f1_gn_{year}_v2.0.nc"
        if key not in objects:
            raise RuntimeError(f"No exact v2 object: {key}")
        result.append(
            {
                "model": model,
                "scenario": scenario,
                "variable": variable,
                "year": year,
                "s3_key": key,
                "global_file_bytes": objects[key],
            }
        )
    return result


def extract(job, site, cache_root, refresh=False):
    point = SITES[site]
    raw = (
        cache_root
        / "nex_cmip6"
        / "raw"
        / site
        / job["model"]
        / job["scenario"]
        / f"{job['variable']}_{job['year']}_v2.0.csv"
    )
    year, var = job["year"], job["variable"]
    params = {
        "var": var,
        "latitude": point["latitude"],
        "longitude": point["longitude"],
        "time_start": f"{year}-01-01T00:00:00Z",
        "time_end": f"{year}-12-31T23:59:59Z",
        "accept": "csv",
    }
    url = NCSS + job["s3_key"].removeprefix("NEX-GDDP-CMIP6/") + "?" + urlencode(params)
    started = time.monotonic()
    cached = raw.exists() and not refresh
    if cached:
        text = raw.read_text()
    else:
        with httpx.Client(
            timeout=180,
            follow_redirects=True,
            transport=httpx.HTTPTransport(local_address="0.0.0.0"),
        ) as client:
            text = get(client, url).text
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    value_col = next((h for h in headers if h.startswith(var + "[")), None)
    if not value_col:
        raise ValueError(f"Unexpected NCSS CSV headers: {headers}")
    expected_unit = "K" if var == "tasmax" else "kg m-2 s-1"
    if value_col != f'{var}[unit="{expected_unit}"]':
        raise ValueError(f"Unexpected units (no automatic guess): {value_col}")
    lat_col = next(h for h in headers if h.startswith("latitude["))
    lon_col = next(h for h in headers if h.startswith("longitude["))
    months, dates, cell = {}, set(), None
    for row in reader:
        date = row["time"][:10]
        if date in dates or not date.startswith(str(year) + "-"):
            raise ValueError(f"Duplicate/wrong-year date {date}")
        dates.add(date)
        v = float(row[value_col])
        if not math.isfinite(v) or abs(v) > 1e10 or (var == "pr" and v < 0):
            raise ValueError(f"Missing/invalid {var} at {date}; cannot publish complete month")
        months.setdefault(date[:7], []).append(v - 273.15 if var == "tasmax" else v * 86400)
        this_cell = [float(row[lat_col]), float(row[lon_col])]
        if cell is not None and cell != this_cell:
            raise ValueError("NCSS changed grid cell within a file")
        cell = this_cell
    values = []
    for month in range(1, 13):
        date = f"{year}-{month:02d}"
        samples = months.get(date, [])
        if len(samples) != calendar.monthrange(year, month)[1]:
            raise ValueError(f"Incomplete month {date}: {len(samples)} days")
        values.append(
            {
                "month": date,
                "value": sum(samples) / len(samples) if var == "tasmax" else sum(samples),
                "n_days": len(samples),
            }
        )
    if not cached:
        raw.parent.mkdir(parents=True, exist_ok=True)
        tmp = raw.with_suffix(".tmp")
        tmp.write_text(text)
        tmp.replace(raw)
    return {
        **job,
        "site": site,
        "cell_lat_lon": cell,
        "url": url,
        "response_bytes": len(text.encode()),
        "seconds": round(time.monotonic() - started, 3),
        "cached": cached,
        "values": values,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sites", nargs="+", choices=SITES, default=["cantho"])
    ap.add_argument(
        "--models",
        nargs="+",
        choices=["ACCESS-CM2", "MPI-ESM1-2-HR"],
        default=["ACCESS-CM2", "MPI-ESM1-2-HR"],
    )
    ap.add_argument("--start-year", type=int, default=2025)
    ap.add_argument("--end-year", type=int, default=2050)
    ap.add_argument("--workers", type=int, choices=range(1, 5), default=3)
    ap.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    if args.start_year > args.end_year:
        ap.error("start-year must be <= end-year")
    start = time.monotonic()
    jobs = []
    with httpx.Client(timeout=60, transport=httpx.HTTPTransport(local_address="0.0.0.0")) as client:
        for model in args.models:
            for scenario in ("ssp245", "ssp585"):
                for variable in ("tasmax", "pr"):
                    jobs.extend(
                        discover(
                            client,
                            model,
                            scenario,
                            variable,
                            args.start_year,
                            args.end_year,
                        )
                    )
    print(
        f"AWS objects={len(jobs)}, global bytes={sum(j['global_file_bytes'] for j in jobs):,}; NCSS point extraction",
        flush=True,
    )
    if args.plan:
        print(__import__("json").dumps(jobs, indent=2))
        return
    results = []
    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        futures = [
            pool.submit(extract, j, s, args.cache_root, args.refresh)
            for s in args.sites
            for j in jobs
        ]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())
            r = results[-1]
            print(
                f"{len(results)}/{len(futures)} {r['site']} {r['model']} {r['scenario']} {r['variable']} {r['year']} {r['seconds']}s",
                flush=True,
            )
    for site in args.sites:
        series = []
        for model in args.models:
            for scenario in ("ssp245", "ssp585"):
                for variable in ("tasmax", "pr"):
                    files = sorted(
                        (
                            r
                            for r in results
                            if (r["site"], r["model"], r["scenario"], r["variable"])
                            == (site, model, scenario, variable)
                        ),
                        key=lambda r: r["year"],
                    )
                    series.append(
                        {
                            "model": model,
                            "scenario": scenario,
                            "variable": variable,
                            "unit": "degC" if variable == "tasmax" else "mm/month",
                            "aggregation": "mean of daily maximum"
                            if variable == "tasmax"
                            else "sum daily precipitation",
                            "values": [v for r in files for v in r["values"]],
                            "files": [{k: v for k, v in r.items() if k != "values"} for r in files],
                        }
                    )
        write_json(
            args.cache_root / "nex_cmip6" / f"{site}.json",
            envelope(
                "NEX-GDDP-CMIP6",
                site,
                evidence_kind="PROJECTION",
                version="2.0",
                method="NCCS NCSS point CSV; AWS key discovery",
                period=[args.start_year, args.end_year],
                probability=None,
                series=series,
                limitations=[
                    "Nearest 0.25 degree cell; not field observation",
                    "Two models are not a probabilistic ensemble",
                    "CMIP6 dates are scenario days, not weather forecasts",
                ],
                elapsed_seconds=round(time.monotonic() - start, 3),
            ),
        )
        if args.start_year == 2025 and args.end_year == 2050:
            import json

            value = json.loads((args.cache_root / "nex_cmip6" / f"{site}.json").read_text())
            write_json(
                ROOT / "apps/api/src/fieldshift/resources/projections" / f"{site}.json", value
            )
    print(f"Done in {time.monotonic() - start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
