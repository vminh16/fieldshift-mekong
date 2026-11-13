#!/usr/bin/env python3
"""ERA5 CDS time-series point CSV, using the REST API with httpx only.

Account: ECMWF/CDS + dataset licence accepted in browser. Key: CDSAPI_KEY env
or `key: PERSONAL-ACCESS-TOKEN` in ~/.cdsapirc (not Earthdata/netrc).
--dry-run prints requests and live date bounds without submitting jobs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import time
import zipfile
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import httpx
from common import DEFAULT_CACHE, SITES, envelope, get, write_json

BASE = "https://cds.climate.copernicus.eu/api"
DATASET = "reanalysis-era5-single-levels-timeseries"
VARIABLES = ["2m_temperature", "total_precipitation"]


def api_key():
    value = os.environ.get("CDSAPI_KEY")
    if not value:
        path = Path.home() / ".cdsapirc"
        if path.exists():
            for line in path.read_text().splitlines():
                if line.strip().startswith("key:"):
                    value = line.split(":", 1)[1].strip().strip("\"'")
    if not value:
        raise RuntimeError(
            "Cần CDSAPI_KEY hoặc ~/.cdsapirc key: PERSONAL-ACCESS-TOKEN; Earthdata không dùng được"
        )
    return value


def csv_tables(data):
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            tables = {
                n: list(csv.DictReader(io.StringIO(z.read(n).decode("utf-8-sig"))))
                for n in z.namelist()
                if n.lower().endswith(".csv")
            }
    else:
        tables = {"data.csv": list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))}
    if not tables or not any(tables.values()):
        raise ValueError("CDS returned no CSV rows")
    # xarray's CSV exporter includes a timestamp and coordinate columns.
    for rows in tables.values():
        if rows and not any("time" in col.lower() or col.lower() == "date" for col in rows[0]):
            raise ValueError("CSV has no recognizable time column")
    return tables


def check_date_coverage(tables, start, end):
    """Reject endpoint-only or truncated output before publishing a cache."""
    expected_days = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    for name, rows in tables.items():
        if not rows:
            raise ValueError("Empty CDS table: " + name)
        time_col = next(col for col in rows[0] if "time" in col.lower() or col.lower() == "date")
        days = {row[time_col][:10] for row in rows}
        if len(days) != expected_days or min(days) != start or max(days) != end:
            raise ValueError(
                "CDS output does not cover requested continuous date interval: " + name
            )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", help="Default: latest allowed date in the live CDS form")
    ap.add_argument("--sites", nargs="+", choices=SITES, default=list(SITES))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--poll-seconds", type=int, choices=range(5, 61), default=30)
    ap.add_argument("--max-wait", type=int, default=10800)
    ap.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    args = ap.parse_args()
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        catalog = get(client, f"{BASE}/catalogue/v1/collections/{DATASET}").json()
        form_url = next(x["href"] for x in catalog["links"] if x["rel"] == "form")
        form = get(client, form_url).json()
        bounds = next(x["details"] for x in form if x.get("name") == "date")
        end = args.end or bounds["maxEnd"]
        if not bounds["minStart"] <= args.start <= end <= bounds["maxEnd"]:
            raise ValueError(
                f"Date range outside current CDS bounds: {bounds['minStart']}..{bounds['maxEnd']}"
            )
        date.fromisoformat(args.start)
        date.fromisoformat(end)
        requests = {
            s: {
                "variable": VARIABLES,
                "date": [f"{args.start}/{end}"],
                "location": {
                    "longitude": SITES[s]["longitude"],
                    "latitude": SITES[s]["latitude"],
                },
                "data_format": "csv",
            }
            for s in args.sites
        }
        if args.dry_run:
            print(
                json.dumps(
                    {"dataset": DATASET, "live_bounds": bounds, "requests": requests},
                    indent=2,
                )
            )
            return
        headers = {"PRIVATE-TOKEN": api_key()}
        for site, request in requests.items():
            fingerprint = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
            job_path = args.cache_root / "era5" / "jobs" / f"{site}_{fingerprint[:16]}.json"
            if job_path.exists():
                job = json.loads(job_path.read_text())
            else:
                response = client.post(
                    f"{BASE}/retrieve/v1/processes/{DATASET}/execution",
                    json={"inputs": request},
                    headers=headers,
                )
                response.raise_for_status()
                job = response.json()
                write_json(job_path, job)  # Persist before polling, no repeated POST on restart.
            job_id = job["jobID"]
            job_url = f"{BASE}/retrieve/v1/jobs/{job_id}"
            print(f"{site}: job={job_id}", flush=True)
            deadline = time.monotonic() + args.max_wait
            while True:
                job = get(client, job_url, headers=headers).json()
                write_json(job_path, job)
                status = job["status"]
                print(f"{site}: {status}", flush=True)
                if status == "successful":
                    break
                if status not in ("accepted", "running", "queued"):
                    raise RuntimeError("CDS job failed: " + json.dumps(job))
                if time.monotonic() >= deadline:
                    raise TimeoutError("CDS job pending; rerun to resume " + job_id)
                time.sleep(args.poll_seconds)
            result_response = get(client, job_url + "/results", headers=headers)
            asset = result_response.json()["asset"]["value"]
            download_url = urljoin(str(result_response.url), asset["href"])
            # No PRIVATE-TOKEN on arbitrary storage URLs or redirects.
            data = get(client, download_url).content
            if len(data) != int(asset["file:size"]):
                raise ValueError("Incomplete CDS download")
            tables = csv_tables(data)
            check_date_coverage(tables, args.start, end)
            write_json(
                args.cache_root / "era5" / f"{site}.json",
                envelope(
                    DATASET,
                    site,
                    evidence_kind="MODEL_ESTIMATE",
                    requested_period=[args.start, end],
                    request=request,
                    job_id=job_id,
                    tables=tables,
                    sha256=hashlib.sha256(data).hexdigest(),
                    value_encoding="Unmodified CDS CSV strings; t2m in K, tp in m; UTC hourly timestamps; coordinates in CSV",
                    limitations=[
                        "Nearest 0.25 degree cell; regional reanalysis, not a field sensor",
                        "Do not re-scale/accumulate precipitation without checking ERA5 accumulation convention",
                        "CSV output schema and multi-variable ZIP packaging need a credentialed live test",
                    ],
                ),
            )


if __name__ == "__main__":
    main()
