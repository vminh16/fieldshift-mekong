#!/usr/bin/env python3
"""Fetch IMERG V07 monthly Final or daily Late windows covering four Mekong sites.

CMR discovery; IPv4 curl with netrc and private persistent session cookies.
Atomic per-granule raw cache and compact processed checkpoints allow safe resume.
"""

from __future__ import annotations

import argparse
import math
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote

import httpx
from common import (
    DEFAULT_CACHE,
    SITES,
    get,
    write_json,
)

CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"


def granules(client, start, end, product="GPM_3IMERGDL"):
    result, page = {}, 1
    while True:
        r = get(
            client,
            CMR,
            params={
                "short_name": product,
                "version": "07",
                "page_size": 2000,
                "page_num": page,
                "sort_key": "start_date",
                "temporal": f"{start}T00:00:00Z,{end}T23:59:59Z",
            },
        )
        entries = r.json()["feed"]["entry"]
        for item in entries:
            result[item["time_start"][:10]] = item
        if len(entries) < 2000:
            break
        page += 1
    return result


def dap_url(item, legacy=False):
    links = [x for x in item["links"] if not x.get("inherited")]
    if legacy:
        data = next(x["href"] for x in links if "/data/GPM_L3/" in x["href"])
        return "https://gpm1.gesdisc.eosdis.nasa.gov/opendap/" + data.split("/data/", 1)[1]
    return next(x["href"] for x in links if "opendap" in x["href"].lower())


def constraint(site):
    p = SITES[site]
    x = min(3599, max(0, math.floor((p["longitude"] + 180) * 10)))
    y = min(1799, max(0, math.floor((p["latitude"] + 90) * 10)))
    return f"precipitation[0:1:0][{x}:1:{x}][{y}:1:{y}]", x, y


def parse_point(text):
    # Hyrax DAP2 Grid: precipitation.precipitation[...] then [0][0], value.
    parts = text.split("---------------------------------------------", 1)
    if len(parts) != 2:
        raise ValueError("Not a Hyrax ASCII data response")
    match = re.search(
        r"(?m)^precipitation(?:\.precipitation)?\[[^\n]*\n\s*\[0\](?:\[0\])*\s*,\s*([^\s,]+)",
        parts[1],
    )
    if not match:
        raise ValueError("Cannot locate precipitation scalar in Hyrax ASCII")
    value = float(match[1])
    return value if math.isfinite(value) and 0 <= value < 1e10 else None


def point_window(sites):
    indices = {site: constraint(site)[1:] for site in sites}
    x0 = min(x for x, y in indices.values())
    x1 = max(x for x, y in indices.values())
    y0 = min(y for x, y in indices.values())
    y1 = max(y for x, y in indices.values())
    return (
        f"precipitation[0:1:0][{x0}:1:{x1}][{y0}:1:{y1}]",
        indices,
        (x0, y0, x1 - x0 + 1, y1 - y0 + 1),
    )


def parse_window(text, indices, bounds):
    """Parse Hyrax and GES DISC DAP2 ASCII, validating the whole window."""
    x0, y0, nx, ny = bounds
    if "---------------------------------------------" in text or re.search(
        r"precipitation\[0\]\[\d+\],", text
    ):
        rows = {
            int(m[1]): [float(v.strip()) for v in m[2].split(",")]
            for m in re.finditer(r"\[0\]\[(\d+)\],\s*([^\n]+)", text)
        }
    else:
        matches = re.findall(r"(?m)^precipitation\.precipitation\[[^\n]+?\],\s*([^\n]+)", text)
        rows = {i: [float(v.strip()) for v in row.split(",")] for i, row in enumerate(matches)}
    if set(rows) != set(range(nx)) or any(len(r) != ny for r in rows.values()):
        raise ValueError("Incomplete or unexpected GES DISC window")
    return {
        site: (v if math.isfinite(v) and 0 <= v < 1e10 else None)
        for site, (x, y) in indices.items()
        for v in [rows[x - x0][y - y0]]
    }


def main():
    import calendar
    import time

    from observations import EarthdataCurl, power_values, publish, stats

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default=date.today().isoformat())
    ap.add_argument("--product", choices=["GPM_3IMERGDL", "GPM_3IMERGM"], default="GPM_3IMERGDL")
    ap.add_argument("--sites", nargs="+", choices=SITES, default=list(SITES))
    ap.add_argument("--legacy", action="store_true")
    ap.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    args = ap.parse_args()
    monthly = args.product == "GPM_3IMERGM"
    source = "imerg_monthly" if monthly else "imerg_late"
    directory = args.cache_root / source
    directory.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=90, transport=httpx.HTTPTransport(local_address="0.0.0.0")) as client:
        catalog = granules(client, args.start, args.end, args.product)
    if not catalog:
        raise RuntimeError("No CMR granules")
    write_json(directory / "catalog.json", catalog)
    ce, indices, bounds = point_window(args.sites)
    curl = EarthdataCurl()
    rows = {site: [] for site in args.sites}
    started = time.monotonic()
    variable = "precipitation_mm_month" if monthly else "precipitation_mm_day"

    def checkpoint():
        for site, series in rows.items():
            reference = power_values(site, "PRECTOTCORR", monthly=monthly)
            compare = stats(
                [
                    (r[variable], reference.get(r["date"][:7] if monthly else r["date"]))
                    for r in series
                ]
            )
            x, y = indices[site]
            publish(
                source,
                site,
                product=args.product,
                version="07",
                variables={
                    variable: {
                        "unit": "mm/month" if monthly else "mm/day",
                        "scale_applied": "rate * 24 * calendar_days" if monthly else 1,
                    }
                },
                resolution="0.1 degree",
                cell={
                    "longitude": round(-179.95 + x * 0.1, 5),
                    "latitude": round(-89.95 + y * 0.1, 5),
                },
                series=series,
                qa={
                    "POWER_PRECTOTCORR": compare,
                    "comparison_unit": "mm/month" if monthly else "mm/day",
                    "note": "UTC grid estimate; no gauge validation. Completion: see progress.json.",
                },
            )
        write_json(
            directory / "progress.json",
            {
                "product": args.product,
                "completed": len(rows[args.sites[0]]),
                "requested": len(catalog),
                "seconds": round(time.monotonic() - started, 2),
                "time_range": [min(catalog), max(catalog)],
                "updated_at": __import__("common").now(),
            },
        )

    try:
        url = dap_url(next(iter(catalog.values())), args.legacy)
        if monthly:
            dds, das = curl.get(url + ".dds"), curl.get(url + ".das")
            (directory / "sample.dds").write_text(dds)
            (directory / "sample.das").write_text(das)
            if not re.search(
                r"Float32 (?:/Grid/)?precipitation\[time = 1\]\[lon = 3600\]\[lat = 1800\]", dds
            ):
                raise ValueError("Unexpected precipitation dimensions")
            block = re.search(r"(?:/Grid/)?precipitation \{(.*?)\}", das, re.S)[1]
            if '"mm/hr"' not in block:
                raise ValueError("Unexpected monthly precipitation units")
        else:
            # V07B includes UInt64 attributes that unconstrained DAP2 DDS/DAS cannot represent.
            # DAP4 metadata is lossless; constrained ASCII precipitation remains DAP2 compatible.
            import xml.etree.ElementTree as ET

            dmr = curl.get(url + ".dmr")
            (directory / "sample.dmr").write_text(dmr)
            root = ET.fromstring(dmr)
            ns = {"d": "http://xml.opendap.org/ns/DAP/4.0#"}
            variable_meta = root.find("d:Float32[@name='precipitation']", ns)
            dimensions = [d.attrib["name"] for d in variable_meta.findall("d:Dim", ns)]
            sizes = {
                d.attrib["name"]: int(d.attrib["size"]) for d in root.findall("d:Dimension", ns)
            }
            unit = variable_meta.find("d:Attribute[@name='units']/d:Value", ns).text
            if (
                dimensions != ["/time", "/lon", "/lat"]
                or sizes.get("lon") != 3600
                or sizes.get("lat") != 1800
                or unit != "mm/day"
            ):
                raise ValueError("Unexpected daily precipitation metadata")
        for n, (iso, item) in enumerate(sorted(catalog.items()), 1):
            raw = directory / "raw" / (iso + ".ascii")
            raw.parent.mkdir(parents=True, exist_ok=True)
            text = (
                raw.read_text()
                if raw.exists()
                else curl.get(dap_url(item, args.legacy) + ".ascii?" + quote(ce, safe=",:."))
            )
            values = parse_window(text, indices, bounds)
            if not raw.exists():
                raw.with_suffix(".tmp").write_text(text)
                raw.with_suffix(".tmp").replace(raw)
            scale = 24 * calendar.monthrange(int(iso[:4]), int(iso[5:7]))[1] if monthly else 1
            for site, value in values.items():
                rows[site].append(
                    {"date": iso, variable: round(value * scale, 6) if value is not None else None}
                )
            if n % 10 == 0 or n == len(catalog) or n == 1:
                checkpoint()
                print(
                    f"{source} {n}/{len(catalog)} {iso} elapsed={time.monotonic() - started:.1f}s",
                    flush=True,
                )
    finally:
        if rows[args.sites[0]]:
            checkpoint()
        curl.close()


if __name__ == "__main__":
    main()
