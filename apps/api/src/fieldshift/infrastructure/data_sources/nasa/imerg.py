"""NASA GPM IMERG V07 Final monthly point series (bundled, produced by scripts/data/fetch_imerg.py)."""

import gzip
import json
from pathlib import Path

RESOURCES = Path(__file__).resolve().parents[3] / "resources" / "observations" / "imerg_monthly"
SOURCE = "NASA GPM IMERG V07 Final monthly"


def load_imerg_monthly(cache_key: str | None) -> dict[tuple[int, int], float] | None:
    """{(year, month): mm} for a bundled demo site; None when the site has no bundle."""
    path = RESOURCES / f"{cache_key}.json.gz"
    if not cache_key or not path.exists():
        return None
    data = json.loads(gzip.decompress(path.read_bytes()))
    return {
        (int(r["date"][:4]), int(r["date"][5:7])): r["precipitation_mm_month"]
        for r in data["series"]
        if r.get("precipitation_mm_month") is not None
    }
