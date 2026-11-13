"""Offline integrity, coverage, unit conversion, comparison and inventory checks on actual artifacts."""

from __future__ import annotations

import calendar
import gzip
import json
import math
from datetime import date

from common import DEFAULT_CACHE, ROOT, SITES
from observations import OBS, power_et0, power_values, stats


def main():
    files = sorted(OBS.glob("*/*.json.gz"))
    required = {
        "source",
        "product",
        "version",
        "variables",
        "spatial_resolution",
        "cell_center",
        "time_range",
        "retrieved_at",
        "qa_note",
        "license",
        "series",
    }
    counts = {}
    for path in files:
        assert path.stat().st_size < 2_000_000, path
        d = json.loads(gzip.decompress(path.read_bytes()))
        assert required <= d.keys(), path
        assert d["series"], path
        assert all({"unit", "scale_applied"} <= m.keys() for m in d["variables"].values()), path
        dates = [r["date"] for r in d["series"]]
        assert d["time_range"] == [min(dates), max(dates)], path
        counts.setdefault(path.parent.name, []).append(len(dates))
        if path.parent.name in ["power", "era5_openmeteo", "imerg_late"]:
            assert len(set(dates)) == len(dates), path
            assert (
                date.fromisoformat(max(dates)) - date.fromisoformat(min(dates))
            ).days + 1 == len(dates), path
        if path.parent.name in ["imerg_monthly", "imerg_late"]:
            monthly = path.parent.name == "imerg_monthly"
            key = "precipitation_mm_month" if monthly else "precipitation_mm_day"
            ref = power_values(path.name.split(".")[0], "PRECTOTCORR", monthly=monthly)
            expected = stats(
                [(r[key], ref.get(r["date"][:7] if monthly else r["date"])) for r in d["series"]]
            )
            assert d["qa_note"]["POWER_PRECTOTCORR"] == expected, path
            assert all(r[key] is None or 0 <= r[key] < 10000 for r in d["series"]), path
        if path.parent.name == "era5_openmeteo":
            ref = power_et0(path.name.split(".")[0])
            expected = stats(
                [(r["et0_fao_evapotranspiration"], ref.get(r["date"])) for r in d["series"]]
            )
            assert d["qa_note"]["POWER_daily"]["et0_fao_evapotranspiration"] == expected, path
            for r in d["series"]:
                lo, hi = r["temperature_2m_min"], r["temperature_2m_max"]
                assert lo is None or hi is None or -20 < lo <= hi < 65, path
                assert r["precipitation_sum"] is None or 0 <= r["precipitation_sum"] < 1500, path
                assert (
                    r["et0_fao_evapotranspiration"] is None
                    or 0 <= r["et0_fao_evapotranspiration"] < 20
                ), path
        if path.parent.name == "imerg_monthly":
            # Independent check of raw rate -> monthly amount at each site's x/y offset.
            point = SITES[path.name.split(".")[0]]
            x = math.floor((point["longitude"] + 180) * 10)
            y = math.floor((point["latitude"] + 90) * 10)
            x0 = min(math.floor((p["longitude"] + 180) * 10) for p in SITES.values())
            y0 = min(math.floor((p["latitude"] + 90) * 10) for p in SITES.values())
            for r in d["series"]:
                text = (DEFAULT_CACHE / "imerg_monthly/raw" / (r["date"] + ".ascii")).read_text()
                line = next(
                    line for line in text.splitlines() if f"precipitation[0][{x - x0}]," in line
                )
                value = float(line.split(",", 1)[1].split(",")[y - y0])
                expected = (
                    value * 24 * calendar.monthrange(int(r["date"][:4]), int(r["date"][5:7]))[1]
                )
                assert math.isclose(r[key], expected, abs_tol=1e-6), path
    inventory = json.loads((ROOT / "docs/data/data_inventory.json").read_text())
    for s in inventory["sources"]:
        assert {
            "source",
            "status",
            "auth",
            "what_we_fetched",
            "files",
            "time_range",
            "latency_days",
            "verified_on",
            "notes",
        } <= s.keys()
        assert s["status"] in inventory["status_values"]
        assert all((ROOT / p).exists() for p in s["files"]), s["source"]
    assert len({s["source"] for s in inventory["sources"]}) == len(inventory["sources"])
    images = list((ROOT / "docs/data/images").glob("*.png"))
    assert len(images) == 12
    assert sum(p.stat().st_size for p in images) < 5_000_000
    print(
        json.dumps(
            {
                "observation_files": len(files),
                "rows_per_site_by_source": counts,
                "largest_gzip_bytes": max(p.stat().st_size for p in files),
                "inventory_sources": len(inventory["sources"]),
                "image_bytes": sum(p.stat().st_size for p in images),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
