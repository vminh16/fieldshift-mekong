#!/usr/bin/env python3
"""Offline protocol/parser checks and independent NEX artifact validation.

Run AFTER fetching the two-model Can Tho demo. Does not write any cache.
uv run --no-project --with httpx python scripts/data/verify_data_access.py --cache-root docs/research/demo-cache
"""

import argparse
import calendar
import csv
import io
import json
import math
import zipfile
from pathlib import Path

import httpx
from common import DEFAULT_CACHE, earthdata_get
from fetch_era5_cds import check_date_coverage, csv_tables
from fetch_imerg import parse_point, parse_window


def protocol_checks():
    visits = []

    def handler(request):
        visits.append((request.url.host, request.headers.get("authorization")))
        if request.url.host == "urs.earthdata.nasa.gov":
            return httpx.Response(302, headers={"location": "https://archive.example/done"})
        if request.url.path == "/start":
            return httpx.Response(
                302,
                headers={"location": "https://urs.earthdata.nasa.gov/oauth/authorize"},
            )
        return httpx.Response(200, text="data")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert (
            earthdata_get(
                client,
                "https://archive.example/start",
                ("local-test-user", "local-test-pass"),
            ).text
            == "data"
        )
    assert [bool(auth) for _, auth in visits] == [False, True, False], visits
    assert visits[1][0] == "urs.earthdata.nasa.gov"
    template = "Dataset {{}}\n---------------------------------------------\nprecipitation.precipitation[1][1][1]\n[0][0], {}\n"
    assert parse_point(template.format("3.25")) == 3.25
    assert parse_point(template.format("-9999.90039")) is None
    window = "Dataset {}\n---------------------------------------------\nprecipitation.precipitation[1][2][2]\n[0][0], 1.25, 2.5\n[0][1], -9999.9, 4.75\nprecipitation.lat[2]\n0, 1\n"
    assert parse_window(window, {"a": (10, 20), "b": (11, 21), "c": (11, 20)}, (10, 20, 2, 2)) == {
        "a": 1.25,
        "b": 4.75,
        "c": None,
    }
    try:
        parse_point("<html>login</html>")
    except ValueError:
        pass
    else:
        raise AssertionError("HTML was mistaken for data")
    content = b"valid_time,latitude,longitude,t2m\n2025-01-01,10,105.75,300\n"
    assert len(csv_tables(content)["data.csv"]) == 1
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as z:
        z.writestr("group.csv", content)
    assert len(csv_tables(output.getvalue())["group.csv"]) == 1
    check_date_coverage(csv_tables(content), "2025-01-01", "2025-01-01")
    try:
        check_date_coverage(
            {"data.csv": [{"time": "2025-01-01"}, {"time": "2025-01-03"}]},
            "2025-01-01",
            "2025-01-03",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Endpoint-only dates were mistaken for continuous coverage")
    return "PASS: URS-only Basic auth; IMERG scalar/fill/HTML; CDS CSV/ZIP"


def verify_nex(root):
    path = root / "nex_cmip6" / "cantho.json"
    data = json.loads(path.read_text())
    assert data["period"] == [2025, 2050]
    assert data["version"] == "2.0"
    assert len(data["series"]) == 8
    count, raw_bytes, global_bytes = 0, 0, 0
    for series in data["series"]:
        assert series["model"] in ("ACCESS-CM2", "MPI-ESM1-2-HR")
        assert series["scenario"] in ("ssp245", "ssp585")
        assert len(series["values"]) == 312
        actual = {row["month"]: row for row in series["values"]}
        for info in series["files"]:
            var, year = info["variable"], info["year"]
            raw = (
                root
                / "nex_cmip6"
                / "raw"
                / "cantho"
                / series["model"]
                / series["scenario"]
                / f"{var}_{year}_v2.0.csv"
            )
            rows = list(csv.DictReader(io.StringIO(raw.read_text())))
            raw_bytes += raw.stat().st_size
            global_bytes += info["global_file_bytes"]
            assert len(rows) == (366 if calendar.isleap(year) else 365)
            value_col = next(col for col in rows[0] if col.startswith(var + "["))
            for month in range(1, 13):
                key = f"{year}-{month:02d}"
                values = [float(r[value_col]) for r in rows if r["time"].startswith(key)]
                assert len(values) == calendar.monthrange(year, month)[1]
                expected = (
                    sum(values) / len(values) - 273.15 if var == "tasmax" else sum(values) * 86400
                )
                assert math.isclose(actual[key]["value"], expected, rel_tol=1e-10, abs_tol=1e-8)
                assert actual[key]["n_days"] == len(values)
                count += 1
    assert count == 2496
    return {
        "monthly_values": count,
        "raw_point_csv_bytes": raw_bytes,
        "aws_global_object_bytes": global_bytes,
        "json_bytes": path.stat().st_size,
        "elapsed_seconds": data["elapsed_seconds"],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--protocol-only", action="store_true")
    args = ap.parse_args()
    print(protocol_checks())
    if not args.protocol_only:
        print(json.dumps(verify_nex(args.cache_root), indent=2))


if __name__ == "__main__":
    main()
