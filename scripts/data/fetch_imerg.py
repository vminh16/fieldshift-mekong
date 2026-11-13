#!/usr/bin/env python3
"""CMR discovery + Hyrax ASCII point daily IMERG Late V07, stdlib + httpx.

--probe requires no credentials: inspect DDS/DAS and the data auth gate.
Real data require ~/.netrc Earthdata credentials. Default = all four sites.
"""

from __future__ import annotations

import argparse
import math
import re
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

import httpx
from common import (
    DEFAULT_CACHE,
    SITES,
    earthdata_credentials,
    earthdata_get,
    envelope,
    get,
    write_json,
)

CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"


def granules(client, start, end):
    result, page = {}, 1
    while True:
        r = get(
            client,
            CMR,
            params={
                "short_name": "GPM_3IMERGDL",
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
    parts = text.split("---------------------------------------------", 1)
    if len(parts) != 2:
        raise ValueError("Not a Hyrax ASCII response")
    block = re.search(
        r"(?m)^precipitation(?:\.precipitation)?\[[^\n]*\n((?:\s*\[0\]\[\d+\],[^\n]*\n?)+)",
        parts[1],
    )
    if not block:
        raise ValueError("Cannot locate precipitation window")
    rows = {
        int(m[1]): [float(v.strip()) for v in m[2].split(",")]
        for m in re.finditer(r"\[0\]\[(\d+)\],\s*([^\n]+)", block[1])
    }
    x0, y0, nx, ny = bounds
    if set(rows) != set(range(nx)) or any(len(r) != ny for r in rows.values()):
        raise ValueError("Incomplete Hyrax window")
    output = {}
    for site, (x, y) in indices.items():
        value = rows[x - x0][y - y0]
        output[site] = value if math.isfinite(value) and 0 <= value < 1e10 else None
    return output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2026-11-01")
    ap.add_argument("--end", default="2026-11-10")
    ap.add_argument("--sites", nargs="+", choices=SITES, default=list(SITES))
    ap.add_argument(
        "--legacy",
        action="store_true",
        help="Use tested legacy gpm1 host; cloud is default",
    )
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    args = ap.parse_args()
    first, last = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if first > last:
        ap.error("start must be <= end")
    credentials = None if args.probe else earthdata_credentials()
    # IPv4 only: IPv6 to URS/GES DISC stalls ~20 s here and breaks TLS handshakes
    transport = httpx.HTTPTransport(local_address="0.0.0.0", retries=2)
    with httpx.Client(timeout=90, follow_redirects=True, transport=transport) as client:
        catalog = granules(client, args.start, args.end)
        if not catalog:
            raise RuntimeError("No CMR granules for requested dates")
        if args.probe:
            import json

            item = next(iter(catalog.values()))
            url = dap_url(item, args.legacy)
            ce, _, _ = point_window(args.sites)
            output = {
                "granule": item["producer_granule_id"],
                "cmr_days": len(catalog),
                "base_url": url,
            }
            for suffix in (".dds", ".das", ".ascii?" + quote(ce, safe=",:.")):
                r = client.get(url + suffix)
                output[suffix] = {
                    "status": r.status_code,
                    "final_host": r.url.host,
                    "body_preview": r.text[:2400],
                }
            print(json.dumps(output, indent=2))
            return
        ce, indices, bounds = point_window(args.sites)
        for_check = next(iter(catalog.values()))
        dds = earthdata_get(client, dap_url(for_check, args.legacy) + ".dds", credentials).text
        if not re.search(r"Float32 precipitation\[time = 1\]\[lon = 3600\]\[lat = 1800\]", dds):
            raise ValueError("Unexpected dimension order; refusing incorrect point indexing")
        all_rows, sources, current = {site: [] for site in args.sites}, [], first
        while current <= last:
            iso = current.isoformat()
            if iso in catalog:
                url = dap_url(catalog[iso], args.legacy) + ".ascii?" + quote(ce, safe=",:.")
                raw_path = (
                    args.cache_root
                    / "imerg_late"
                    / "raw"
                    / (catalog[iso]["producer_granule_id"] + "_" + str(bounds) + ".ascii")
                )
                text = (
                    raw_path.read_text()
                    if raw_path.exists()
                    else earthdata_get(client, url, credentials).text
                )
                values = parse_window(text, indices, bounds)
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = raw_path.with_suffix(".tmp")
                tmp.write_text(text)
                tmp.replace(raw_path)
                sources.append(url)
            else:
                values = {site: None for site in args.sites}
            for site in args.sites:
                quality = (
                    "GRANULE_UNAVAILABLE"
                    if iso not in catalog
                    else "VALUE_PRESENT_QA_NOT_EVALUATED"
                    if values[site] is not None
                    else "FILL_OR_INVALID"
                )
                all_rows[site].append(
                    {
                        "date": iso,
                        "precipitation_mm_day": values[site],
                        "quality": quality,
                    }
                )
            current += timedelta(days=1)
        for site, rows in all_rows.items():
            x, y = indices[site]
            write_json(
                args.cache_root / "imerg_late" / f"{site}.json",
                envelope(
                    "GPM_3IMERGDL",
                    site,
                    version="07",
                    evidence_kind="OBSERVED_REMOTE_ESTIMATE",
                    units={"precipitation_mm_day": "mm/day"},
                    cell={
                        "longitude": round(-179.95 + x * 0.1, 5),
                        "latitude": round(-89.95 + y * 0.1, 5),
                    },
                    period=[args.start, args.end],
                    values=rows,
                    source_urls=sources,
                    limitations=[
                        "Daily mean rate already in mm/day: do not multiply by 24",
                        "UTC day; satellite grid estimate, not canal salinity",
                    ],
                ),
            )
            print(f"{site}: {len(rows)} days")


if __name__ == "__main__":
    main()
