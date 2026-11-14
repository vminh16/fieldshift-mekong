"""Small validated observation bundles, comparison statistics and IPv4 curl access."""

from __future__ import annotations

import calendar
import gzip
import json
import math
import os
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

from common import ROOT, now

OBS = ROOT / "apps/api/src/fieldshift/resources/observations"


def publish(
    source,
    site,
    *,
    product,
    version,
    variables,
    resolution,
    cell,
    series,
    qa,
    license="NASA Earth science open data",
    **extra,
):
    dates = [r["date"] for r in series]
    payload = dict(
        source=source,
        product=product,
        version=version,
        variables=variables,
        spatial_resolution=resolution,
        cell_center=cell,
        time_range=[min(dates), max(dates)] if dates else None,
        retrieved_at=now(),
        qa_note=qa,
        license=license,
        series=series,
        **extra,
    )
    data = gzip.compress(
        json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode(),
        mtime=0,
    )
    if len(data) >= 2_000_000:
        raise ValueError("Observation bundle exceeds 2 MB")
    path = OBS / source / (site + ".json.gz")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    return path


def power(site):
    path = ROOT / f"apps/api/src/fieldshift/resources/demo_cache/power/{site}.json.gz"
    data = json.loads(gzip.decompress(path.read_bytes()))
    return data.get("payload", data)


def stats(pairs):
    pairs = [
        (a, b)
        for a, b in pairs
        if a is not None and b is not None and math.isfinite(a) and math.isfinite(b)
    ]
    if not pairs:
        return {"n": 0, "bias": None, "correlation": None}
    n = len(pairs)
    a = sum(x for x, _ in pairs) / n
    b = sum(y for _, y in pairs) / n
    va = sum((x - a) ** 2 for x, _ in pairs)
    vb = sum((y - b) ** 2 for _, y in pairs)
    return {
        "n": n,
        "bias": round(a - b, 5),
        "correlation": round(sum((x - a) * (y - b) for x, y in pairs) / math.sqrt(va * vb), 6)
        if va * vb
        else None,
        "bias_definition": "source minus POWER",
    }


def power_values(site, variable, monthly=False):
    data = power(site)
    values = data["properties"]["parameter"][variable]
    clean = {
        f"{k[:4]}-{k[4:6]}-{k[6:8]}": v for k, v in values.items() if v is not None and v > -900
    }
    if not monthly:
        return clean
    months = defaultdict(list)
    for d, v in clean.items():
        months[d[:7]].append(v)
    return {
        m: sum(v)
        for m, v in months.items()
        if len(v) == calendar.monthrange(int(m[:4]), int(m[5:7]))[1]
    }


class EarthdataCurl:
    """Credentials stay in netrc; private cookie file is removed on close."""

    def __init__(self):
        fd, self.cookies = tempfile.mkstemp(prefix="fieldshift-cookies-")
        os.close(fd)

    def close(self):
        Path(self.cookies).unlink(missing_ok=True)

    def get(self, url):
        result = subprocess.run(
            [
                "curl",
                "-4",
                "--netrc",
                "--location",
                "--silent",
                "--show-error",
                "--fail",
                "--retry",
                "3",
                "--connect-timeout",
                "20",
                "--max-time",
                "180",
                "--cookie-jar",
                self.cookies,
                "--cookie",
                self.cookies,
                "--globoff",
                url,
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(f"curl failed (exit {result.returncode}); no response logged")
        text = result.stdout.decode()
        if "<html" in text[:1000].lower() or "<!doctype html" in text[:1000].lower():
            raise RuntimeError("Earthdata returned HTML instead of data")
        return text


def power_et0(site):
    """Independent reference ET0 from POWER using the project's FAO-56 implementation."""
    import sys

    sys.path.insert(0, str(ROOT / "apps/api/src"))
    from fieldshift.infrastructure.crop_models.fao56_water import et0_pm, weather_from_power

    payload = power(site)
    elevation = json.loads(
        (ROOT / f"apps/api/src/fieldshift/resources/demo_cache/srtm/{site}.json").read_text()
    )["elevation"]
    out = {}
    for row in weather_from_power(payload):
        names = ["tmax", "tmin", "tdew", "rs_mj", "u2"]
        if all(row[k] is not None and row[k] > -900 for k in names):
            d = row["date"]
            out[d.isoformat()] = et0_pm(
                d.timetuple().tm_yday,
                __import__("common").SITES[site]["latitude"],
                elevation,
                *(row[k] for k in names),
            )
    return out
