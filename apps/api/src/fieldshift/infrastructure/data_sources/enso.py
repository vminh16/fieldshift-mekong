"""NOAA ONI (Oceanic Niño Index) adapter: bundled file, no network at plan time.

Refresh with scripts/data/fetch_oni.py. Each monthly value is the 3-month running mean of
Niño-3.4 SST anomalies CENTRED on that month (Sep = Aug–Sep–Oct, "ASO").

No look-ahead (AC-04): a centred month m is usable at as_of only if its window END month
(m + 1) is strictly before as_of's calendar month, i.e. the whole window has finished
before the month of planning. as_of 2026-11-14 -> 2026-09 (ASO); 2015-11-15 -> 2015-09.
"""

import datetime as dt
from functools import lru_cache
from pathlib import Path

ONI_FILE = Path(__file__).resolve().parents[2] / "resources" / "enso" / "oni.data"
SOURCE = "NOAA PSL ONI (CPC, ERSSTv6)"
SOURCE_URL = "https://psl.noaa.gov/data/correlation/oni.data"
RETRIEVED = "2026-11-14"
LICENCE = "NOAA data, U.S. public domain"
MISSING = -99.9


@lru_cache
def load_oni(path: Path = ONI_FILE) -> dict[tuple[int, int], float]:
    """{(year, centred_month): value}, missing values dropped."""
    out = {}
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) != 13 or not parts[0].isdigit():
            continue  # header "1950 2026", trailer lines
        for month, raw in enumerate(parts[1:], start=1):
            value = float(raw)
            if value > MISSING + 0.01:
                out[(int(parts[0]), month)] = value
    return out


def latest_oni(as_of: dt.date, oni: dict | None = None) -> tuple[int, int, float] | None:
    """(year, centred_month, value) of the latest ONI whose window ended before as_of's month."""
    oni = load_oni() if oni is None else oni
    # centred month index c is usable iff c + 1 < as_of month index
    limit = as_of.year * 12 + as_of.month - 1 - 2  # 0-based month index of latest usable centre
    usable = [k for k in oni if k[0] * 12 + k[1] - 1 <= limit]
    if not usable:
        return None
    y, m = max(usable)
    return y, m, oni[(y, m)]
