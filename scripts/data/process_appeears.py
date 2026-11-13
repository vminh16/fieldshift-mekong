"""Validate completed AppEEARS bundles and publish physical-unit series; optionally watch both tasks.

Point CSV values are already scaled by AppEEARS. Never apply raster ScaleFactor twice.
All row QA columns are retained. No interpolation or substitution for cloud/missing values.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import time
from datetime import datetime
from pathlib import Path

import httpx
from common import DEFAULT_CACHE, SITES, get, write_json
from observations import publish

PRODUCTS = {
    "SPL4SMGP.008": (
        "smap",
        ["Geophysical_Data_sm_surface", "Geophysical_Data_sm_rootzone"],
        "9 km EASE-2",
    ),
    "MOD13Q1.061": ("modis_vi", ["_250m_16_days_NDVI", "_250m_16_days_EVI"], "250 m"),
    "MOD16A2GF.061": ("modis_et", ["ET_500m"], "500 m"),
    "ECO_L2T_LSTE.002": ("ecostress_lst", ["LST", "LST_err", "QC", "cloud"], "70 m"),
    "ECO_L3T_JET.002": ("ecostress_et", ["ETdaily", "cloud"], "70 m"),
    "HLSL30_VI.020": ("hls_l30", ["NDVI"], "30 m"),
    "HLSS30_VI.020": ("hls_s30", ["NDVI"], "30 m"),
}


def numeric(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError):
        return None


def iso_date(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass
    for fmt in ["%Y-%m-%d", "%m-%d-%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%m/%d/%Y"]:
        try:
            return datetime.strptime(value, fmt).isoformat()[:10]
        except ValueError:
            pass
    raise ValueError("Unexpected AppEEARS date format")


def product_matches(path, product):
    def normalized(value):
        return re.sub(r"[^a-z0-9]", "", value.lower())

    return normalized(product) in normalized(path.name)


def process(directory, client):
    bundle = json.loads((directory / "bundle.json").read_text())
    for item in bundle["files"]:
        path = directory / Path(item["file_name"]).name
        if not path.exists() or path.stat().st_size != item["file_size"]:
            return False
        if item.get("sha256") and hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("AppEEARS bundle checksum mismatch: " + path.name)
    metadata = {}
    result_tables = {}
    for product in PRODUCTS:
        paths = [
            p
            for p in directory.glob("*.csv")
            if product_matches(p, product) and "results" in p.name.lower()
        ]
        if paths:
            metadata[product] = get(
                client, "https://appeears.earthdatacloud.nasa.gov/api/product/" + product
            ).json()
            result_tables[product] = []
            for path in paths:
                with path.open(encoding="utf-8-sig", newline="") as f:
                    result_tables[product].extend(csv.DictReader(f))
    if not result_tables:
        raise ValueError("Completed bundle has no recognized product result tables")
    write_json(directory / "layer_metadata.json", metadata)
    summaries = {}
    for product, raw_rows in result_tables.items():
        source, layers, resolution = PRODUCTS[product]
        meta = metadata[product]
        for site in SITES:
            rows = [r for r in raw_rows if r.get("ID", r.get("id")) == site]
            if not rows:
                continue
            fieldnames = list(rows[0])
            mapping = {}
            for layer in layers:
                # Exact suffix is required so NDVI is never mistaken for detailed QA.
                candidates = [
                    h for h in fieldnames if h.endswith(layer) or h.endswith(layer.lstrip("_"))
                ]
                if not candidates:
                    raise ValueError(
                        "Missing expected CSV layer "
                        + product
                        + "/"
                        + layer
                        + "; columns="
                        + str(fieldnames)
                    )
                mapping[layer] = min(candidates, key=len)
            variables = {
                layer: {
                    "unit": meta[layer].get("Units")
                    or ("1" if layer.endswith(("NDVI", "EVI")) else "QA code"),
                    "scale_applied": "AppEEARS point CSV already applies product scaling; local multiplier 1",
                    "native_scale_factor": meta[layer].get("ScaleFactor"),
                    "native_add_offset": meta[layer].get("AddOffset"),
                }
                for layer in layers
            }
            series = []
            valid = {layer: 0 for layer in layers}
            cloudy = 0
            cloud_known = 0
            for raw in rows:
                record = {"date": iso_date(raw["Date"])}
                if len(raw["Date"]) > 10:
                    record["timestamp"] = raw["Date"]
                for name in ["Time", "DateTime", "Observation", "Granule", "Filename"]:
                    if raw.get(name):
                        record[name.lower()] = raw[name]
                qa = {
                    h: v
                    for h, v in raw.items()
                    if any(w in h.lower() for w in ["qa", "quality", "cloud", "fmask"])
                }
                record["qa"] = qa
                for layer, column in mapping.items():
                    value = numeric(raw[column])
                    m = meta[layer]
                    fills = [numeric(x) for x in m.get("FillValueAll", [m.get("FillValue")])]
                    if value in fills:
                        value = None
                    lo, hi = numeric(m.get("ValidMin")), numeric(m.get("ValidMax"))
                    if value is not None and (
                        (lo is not None and value < lo) or (hi is not None and value > hi)
                    ):
                        value = None
                    record[layer] = value
                    valid[layer] += value is not None
                cloud = record.get("cloud")
                if cloud is not None:
                    cloud_known += 1
                    cloudy += cloud != 0
                series.append(record)
            # Distinguish value-present counts from cloud-cleared/QA-accepted counts.
            qa_note = {
                "task_id": bundle["task_id"],
                "raw_rows": len(rows),
                "valid_value_counts": valid,
                "cloud_fraction": cloudy / cloud_known if cloud_known else None,
                "cloud_known_count": cloud_known,
                "qa_accepted_count": None,
                "note": "Values already scaled by AppEEARS. QA retained; value-present counts are NOT necessarily cloud-clear. HLS VI must be joined to corresponding Fmask by acquisition before scientific interpretation. Composite ET is per composite, including shorter final annual period; not ET0.",
                "scaling_reference": "https://forum.earthdata.nasa.gov/viewtopic.php?t=5682",
            }
            # AppEEARS point CSV gives requested coordinates; pixel centers are not returned reliably.
            publish(
                source,
                site,
                product=product,
                version=product.rsplit(".", 1)[1],
                variables=variables,
                resolution=resolution,
                cell=None,
                series=series,
                qa=qa_note,
                requested_point=SITES[site],
                cell_center_note="[UNVERIFIED] AppEEARS point CSV coordinate is requested point; native cell center not independently geolocated.",
                task_id=bundle["task_id"],
            )
            summaries.setdefault(source, {})[site] = {
                "rows": len(series),
                "time_range": [min(r["date"] for r in series), max(r["date"] for r in series)],
                "valid": valid,
                "cloud_fraction": qa_note["cloud_fraction"],
            }
    # Keep HLS Fmask as a separate acquisition series, preserving possible date/scene ambiguity.
    for product in ["HLSL30.020", "HLSS30.020"]:
        paths = [p for p in directory.glob("*results.csv") if product_matches(p, product)]
        for path in paths:
            with path.open(encoding="utf-8-sig") as f:
                raw_rows = list(csv.DictReader(f))
            for site in SITES:
                rows = [r for r in raw_rows if r.get("ID", r.get("id")) == site]
                if not rows:
                    continue
                col = next(h for h in rows[0] if h.endswith("Fmask"))
                series = [
                    {
                        "date": iso_date(r["Date"]),
                        "fmask": numeric(r[col]),
                        "qa": {h: v for h, v in r.items() if "Fmask" in h},
                    }
                    for r in rows
                ]
                masks = [
                    int(r["fmask"])
                    for r in series
                    if r["fmask"] is not None and 0 <= r["fmask"] < 255
                ]
                clear = sum((v & 0b11111) == 0 for v in masks)
                source = "hls_l30_qa" if "L30" in product else "hls_s30_qa"
                publish(
                    source,
                    site,
                    product=product,
                    version="020",
                    variables={"fmask": {"unit": "bitmask", "scale_applied": 1}},
                    resolution="30 m",
                    cell=None,
                    series=series,
                    qa={
                        "cloud_fraction": sum(bool(v & 0b1111) for v in masks) / len(masks)
                        if masks
                        else None,
                        "valid_masks": len(masks),
                        "clear_no_shadow_snow_count": clear,
                        "note": "HLS bits 0 cirrus,1 cloud,2 adjacent cloud,3 shadow,4 snow. Water bit retained. Join VI by acquisition; do not equate same date to same scene without checking.",
                    },
                )
    write_json(directory / "processed_summary.json", summaries)
    print("processed", bundle["task_id"], summaries, flush=True)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--watch", action="store_true")
    args = ap.parse_args()
    done = set()
    with httpx.Client(timeout=90, transport=httpx.HTTPTransport(local_address="0.0.0.0")) as client:
        while True:
            for directory in (DEFAULT_CACHE / "appeears/bundles").glob("*"):
                if directory.name not in done and (directory / "bundle.json").exists():
                    if process(directory, client):
                        done.add(directory.name)
            if not args.watch or len(done) >= 2:
                break
            time.sleep(30)


if __name__ == "__main__":
    main()
