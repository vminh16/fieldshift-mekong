#!/usr/bin/env python3
"""One AppEEARS point task: 4 sites, SMAP L4 v008 + MODIS NDVI/EVI + ET.

stdlib + httpx; Earthdata login/password only from ~/.netrc.
--dry-run validates the public catalog and prints the exact JSON, no login.
Without --dry-run: submit once, persist task id, resume/poll/download with SHA256.
Raw CSV strings and all QA columns are preserved; no guessed rescaling/filtering.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import time
from datetime import date
from pathlib import Path

import httpx
from common import (
    DEFAULT_CACHE,
    SITES,
    earthdata_credentials,
    envelope,
    get,
    write_json,
)

API = "https://appeears.earthdatacloud.nasa.gov/api"
LAYERS = [
    {"product": "SPL4SMGP.008", "layer": "Geophysical_Data_sm_surface"},
    {"product": "SPL4SMGP.008", "layer": "Geophysical_Data_sm_rootzone"},
    {"product": "MOD13Q1.061", "layer": "_250m_16_days_NDVI"},
    {"product": "MOD13Q1.061", "layer": "_250m_16_days_EVI"},
    {"product": "MOD16A2GF.061", "layer": "ET_500m"},
]


def task_body(start="2015-01-01", end="2026-11-10"):
    return {
        "task_type": "point",
        "task_name": "FieldShift Mekong demo 2015-2026",
        "params": {
            "dates": [
                {
                    "startDate": date.fromisoformat(start).strftime("%m-%d-%Y"),
                    "endDate": date.fromisoformat(end).strftime("%m-%d-%Y"),
                }
            ],
            "layers": LAYERS,
            "coordinates": [
                {
                    "id": site,
                    "category": site,
                    "latitude": p["latitude"],
                    "longitude": p["longitude"],
                }
                for site, p in SITES.items()
            ],
        },
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", default="2026-11-10")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--task-id", help="Resume an existing task instead of submission")
    ap.add_argument("--poll-seconds", type=int, choices=range(5, 61), default=30)
    ap.add_argument("--max-wait", type=int, default=10800)
    ap.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    args = ap.parse_args()
    if date.fromisoformat(args.start) > date.fromisoformat(args.end):
        ap.error("start must be <= end")
    body = task_body(args.start, args.end)
    body_hash = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    state_path = args.cache_root / "appeears" / "task.json"
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        products = {p["ProductAndVersion"]: p for p in get(client, API + "/product").json()}
        metadata = {}
        for product in sorted({x["product"] for x in LAYERS}):
            if not products.get(product, {}).get("Available"):
                raise RuntimeError(f"Product unavailable: {product}")
            metadata[product] = get(client, API + "/product/" + product).json()
        for layer in LAYERS:
            if not metadata[layer["product"]].get(layer["layer"], {}).get("Available"):
                raise RuntimeError(f"Layer unavailable: {layer}")
        if args.dry_run:
            print(json.dumps(body, ensure_ascii=False, indent=2))
            return
        credentials = earthdata_credentials()

        def login():
            # Official Basic-auth flow, Content-Length: 0; credentials from netrc.
            r = client.post(API + "/login", auth=httpx.BasicAuth(*credentials), content=b"")
            r.raise_for_status()
            return {"Authorization": "Bearer " + r.json()["token"]}

        headers = login()

        def authenticated_get(path):
            nonlocal headers
            r = client.get(API + path, headers=headers)
            if r.status_code == 401:
                headers = login()
                r = client.get(API + path, headers=headers)
            r.raise_for_status()
            return r

        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        if args.task_id:
            # Confirm this task describes exactly these points/dates/layers.
            existing = authenticated_get("/task/" + args.task_id).json()
            if existing.get("params") != body["params"]:
                raise RuntimeError("Existing task params differ from requested points/dates/layers")
            task_id = args.task_id
        elif state.get("body_sha256") == body_hash:
            task_id = state["task_id"]
        else:
            # Never retry an ambiguous POST: a retry could create duplicate expensive jobs.
            r = client.post(API + "/task", json=body, headers=headers)
            r.raise_for_status()
            task_id = r.json()["task_id"]
        state = {"task_id": task_id, "body_sha256": body_hash, "request": body}
        write_json(state_path, state)
        print("AppEEARS task_id=" + task_id, flush=True)
        deadline = time.monotonic() + args.max_wait
        while True:
            status = authenticated_get("/task/" + task_id).json()
            state["status"] = status.get("status")
            write_json(state_path, state)
            print("status=" + str(state["status"]), flush=True)
            if state["status"] == "done":
                break
            if state["status"] in ("error", "failed", "cancelled", "canceled"):
                raise RuntimeError("AppEEARS task failed: " + json.dumps(status))
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Task still pending; rerun to resume {task_id}")
            time.sleep(args.poll_seconds)
        bundle = authenticated_get("/bundle/" + task_id).json()
        directory = args.cache_root / "appeears" / "bundles" / task_id
        directory.mkdir(parents=True, exist_ok=True)
        write_json(directory / "bundle.json", bundle)
        tables = {site: {} for site in SITES}
        for item in bundle["files"]:
            path = directory / Path(item["file_name"]).name
            expected = item.get("sha256")
            data = path.read_bytes() if path.exists() else None
            if data is None or (expected and hashlib.sha256(data).hexdigest() != expected):
                data = authenticated_get("/bundle/" + task_id + "/" + item["file_id"]).content
                if expected and hashlib.sha256(data).hexdigest() != expected:
                    raise ValueError("SHA256 mismatch: " + path.name)
                if len(data) != item["file_size"]:
                    raise ValueError("Incomplete download: " + path.name)
                tmp = path.with_suffix(path.suffix + ".tmp")
                tmp.write_bytes(data)
                tmp.replace(path)
            if path.suffix.lower() != ".csv":
                continue
            reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
            id_col = next((h for h in (reader.fieldnames or []) if h.lower() == "id"), None)
            if not id_col:  # lookup/statistics CSV, retained in bundle
                continue
            for row in reader:
                site = row[id_col]
                if site not in tables:
                    raise ValueError("Unrecognized AppEEARS point ID: " + site)
                tables[site].setdefault(path.name, []).append(row)
        selected_metadata = {
            x["product"] + "/" + x["layer"]: metadata[x["product"]][x["layer"]] for x in LAYERS
        }
        for site in SITES:
            if not tables[site]:
                raise ValueError("No data rows for site " + site)
            write_json(
                args.cache_root / "appeears" / f"{site}.json",
                envelope(
                    "AppEEARS",
                    site,
                    task_id=task_id,
                    requested_period=[args.start, args.end],
                    tables=tables[site],
                    layer_metadata=selected_metadata,
                    evidence_kind={
                        "SPL4SMGP.008": "MODEL_ESTIMATE",
                        "MOD13Q1.061": "OBSERVED_REMOTE_ESTIMATE",
                        "MOD16A2GF.061": "MODEL_ESTIMATE",
                    },
                    value_encoding="Original AppEEARS CSV strings, service units; QA retained; no second scaling",
                    limitations=[
                        "Requested interval does not guarantee available dates",
                        "SMAP starts 2015-03-31",
                        "MOD16A2GF is year-end gap-filled; current year may be absent",
                        "Inspect QA and bundle metadata before model ingestion",
                    ],
                ),
            )
            print(f"{site}: {sum(map(len, tables[site].values()))} CSV rows")


if __name__ == "__main__":
    main()
