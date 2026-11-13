"""Shared point locations, HTTP handling and atomic caches (stdlib + httpx)."""

from __future__ import annotations

import json
import netrc
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = ROOT / ".fieldshift/cache"  # gitignored
SITES = {
    "cantho": {"name": "Cần Thơ", "latitude": 10.03, "longitude": 105.78},
    "chaudoc": {"name": "Châu Đốc", "latitude": 10.70, "longitude": 105.12},
    "bentre": {"name": "Bến Tre", "latitude": 10.10, "longitude": 106.45},
    "soctrang": {"name": "Sóc Trăng", "latitude": 9.55, "longitude": 106.20},
}


def now():
    return datetime.now(UTC).isoformat()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def earthdata_credentials():
    try:
        entry = netrc.netrc().authenticators("urs.earthdata.nasa.gov")
    except (OSError, netrc.NetrcParseError) as e:
        raise RuntimeError(
            "Cần ~/.netrc: machine urs.earthdata.nasa.gov login USER password PASS (chmod 600)"
        ) from e
    if not entry or not entry[0] or not entry[2]:
        raise RuntimeError("Thiếu Earthdata login/password trong ~/.netrc")
    return entry[0], entry[2]


def get(client, url, **kwargs):
    """Retry transient GET failures; POST submissions are deliberately not retried."""
    for attempt in range(4):
        try:
            r = client.get(url, **kwargs)
            if r.status_code not in (429, 500, 502, 503, 504) or attempt == 3:
                r.raise_for_status()
                return r
        except httpx.TransportError:
            if attempt == 3:
                raise
        time.sleep(2**attempt)
    raise RuntimeError("GET retries exhausted")


def earthdata_get(client, url, credentials):
    """Cookie OAuth redirects; Basic credentials go ONLY to the exact URS host."""
    current = httpx.URL(url)
    for _ in range(20):
        if current.scheme != "https":
            raise RuntimeError("Refusing non-HTTPS Earthdata redirect")
        auth = httpx.BasicAuth(*credentials) if current.host == "urs.earthdata.nasa.gov" else None
        r = client.get(current, auth=auth, follow_redirects=False)
        if r.status_code in (301, 302, 303, 307, 308):
            current = r.url.join(r.headers["location"])
            continue
        r.raise_for_status()
        if "text/html" in r.headers.get("content-type", ""):
            raise RuntimeError(
                "Earthdata returned HTML login/consent page; approve archive application in URS profile"
            )
        return r
    raise RuntimeError("Earthdata redirect loop: approve archive application in URS profile")


def envelope(source, site, **data):
    return {
        "schema_version": 1,
        "source": source,
        "site": {"id": site, **SITES[site]},
        "retrieved_at": now(),
        "spatial_scale": "regional",
        **data,
    }
