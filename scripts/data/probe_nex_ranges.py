#!/usr/bin/env python3
"""Measure AWS HDF5 range extraction, without downloading an entire year.

Optional diagnostic dependencies: httpx, h5netcdf, h5py (h5netcdf backend).
uv run --no-project --with httpx --with h5netcdf --with h5py python scripts/data/probe_nex_ranges.py
The production NCSS fetcher needs only httpx. Output is JSON on stdout.
"""

import argparse
import io
import json
import time

import h5netcdf
import httpx
from common import SITES


def string(value):
    return value.decode() if isinstance(value, bytes) else str(value)


class HTTPRangeFile(io.RawIOBase):
    def __init__(self, url, max_bytes):
        self.client = httpx.Client(timeout=90)
        self.url, self.pos, self.bytes, self.requests = url, 0, 0, 0
        r = self.client.head(url)
        r.raise_for_status()
        self.size = int(r.headers["content-length"])
        self.max_bytes = max_bytes
        self.small_cache = {}

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = (
            offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        )
        if self.pos < 0:
            raise ValueError("Negative seek")
        return self.pos

    def readinto(self, buf):
        data = self.read(len(buf))
        buf[: len(data)] = data
        return len(data)

    def read(self, count=-1):
        if count < 0:
            count = self.size - self.pos
        count = min(count, self.size - self.pos)
        if count <= 0:
            return b""
        key = (self.pos, count)
        if key in self.small_cache:
            data = self.small_cache[key]
        else:
            if self.bytes + count > self.max_bytes:
                raise RuntimeError("Range probe byte budget exceeded")
            r = self.client.get(
                self.url, headers={"Range": f"bytes={self.pos}-{self.pos + count - 1}"}
            )
            r.raise_for_status()
            if r.status_code != 206 or len(r.content) != count:
                raise RuntimeError("Server ignored Range or returned incomplete bytes")
            data = r.content
            self.requests += 1
            self.bytes += len(data)
            if count <= 65536:
                self.small_cache[key] = data
        self.pos += len(data)
        return data


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="ACCESS-CM2")
    ap.add_argument("--variable", choices=["tasmax", "pr"], default="tasmax")
    ap.add_argument("--scenario", choices=["ssp245", "ssp585"], default="ssp245")
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--max-mib", type=int, default=16)
    args = ap.parse_args()
    v, m, s, y = args.variable, args.model, args.scenario, args.year
    url = f"https://nex-gddp-cmip6.s3.amazonaws.com/NEX-GDDP-CMIP6/{m}/{s}/r1i1p1f1/{v}/{v}_day_{m}_{s}_r1i1p1f1_gn_{y}_v2.0.nc"
    started = time.monotonic()
    remote = HTTPRangeFile(url, args.max_mib * 1024**2)
    try:
        with h5netcdf.File(remote, "r") as f:
            variable = f.variables[v]
            lat, lon = f.variables["lat"][:], f.variables["lon"][:]
            cells = {
                site: (
                    int(abs(lat - p["latitude"]).argmin()),
                    int(abs(lon - p["longitude"]).argmin()),
                )
                for site, p in SITES.items()
            }
            result = {
                "url": url,
                "global_file_bytes": remote.size,
                "shape": variable.shape,
                "chunks": variable.chunks,
                "units": string(variable.attrs["units"]),
                "version": string(f.attrs["version"]),
                "calendar": string(f.variables["time"].attrs["calendar"]),
                "cells": {
                    site: {
                        "index_lat_lon": [a, b],
                        "lat_lon": [float(lat[a]), float(lon[b])],
                    }
                    for site, (a, b) in cells.items()
                },
                "sample": [],
            }
            for day in range(min(args.days, variable.shape[0])):
                # The stored chunk is global: read/decompress once, reuse for all sites.
                slab = variable[day, :, :]
                result["sample"].append(
                    {
                        "day_index": day,
                        **{site: float(slab[a, b]) for site, (a, b) in cells.items()},
                    }
                )
            result.update(
                {
                    "http_range_requests": remote.requests,
                    "downloaded_bytes": remote.bytes,
                    "seconds": round(time.monotonic() - started, 3),
                    "tested": True,
                }
            )
            print(json.dumps(result, indent=2, allow_nan=False))
    finally:
        remote.client.close()


if __name__ == "__main__":
    main()
