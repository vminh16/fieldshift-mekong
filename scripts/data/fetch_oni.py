"""Refresh the bundled NOAA PSL ONI file (the planner itself never fetches it).

    python scripts/data/fetch_oni.py
Source: https://psl.noaa.gov/data/correlation/oni.data (NOAA, U.S. public domain).
After refreshing, update RETRIEVED in fieldshift/infrastructure/data_sources/enso.py.
"""

from pathlib import Path

import httpx

URL = "https://psl.noaa.gov/data/correlation/oni.data"
OUT = Path(__file__).resolve().parents[2] / "apps/api/src/fieldshift/resources/enso/oni.data"


def main() -> None:
    r = httpx.get(URL, timeout=60, follow_redirects=True)
    r.raise_for_status()
    rows = [line.split() for line in r.text.splitlines()]
    if sum(len(p) == 13 and p[0].isdigit() for p in rows) < 70:  # 1950..present
        raise SystemExit("Unexpected ONI format; bundled file left unchanged")
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(r.text)
    tmp.replace(OUT)  # atomic: a failed download never leaves a half-written file
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
