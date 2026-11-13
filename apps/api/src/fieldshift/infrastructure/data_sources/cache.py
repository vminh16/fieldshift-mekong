"""File cache (cache-aside). Writable dir from settings; read-only bundled demo cache as fallback."""

import gzip
import json
from pathlib import Path

from fieldshift.settings import get_settings

BUNDLED = Path(__file__).resolve().parents[2] / "resources" / "demo_cache"


def key_for(lat: float, lon: float, cache_key: str | None) -> str:
    return cache_key or f"{lat:.2f}_{lon:.2f}"


def _writable(source: str, key: str) -> Path:
    return get_settings().data_dir / "cache" / source / f"{key}.json"


def read(source: str, key: str) -> dict | None:
    for f in (_writable(source, key), BUNDLED / source / f"{key}.json"):
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
    gz = BUNDLED / source / f"{key}.json.gz"
    if gz.exists():
        return json.loads(gzip.decompress(gz.read_bytes()))
    return None


def write(source: str, key: str, text: str) -> None:
    f = _writable(source, key)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


def all_entries(source: str):
    """Yield every cached payload for a source (writable + bundled)."""
    dirs = [get_settings().data_dir / "cache" / source, BUNDLED / source]
    for d in dirs:
        for f in sorted(d.glob("*.json*")) if d.exists() else []:
            raw = f.read_bytes()
            yield json.loads(gzip.decompress(raw) if f.suffix == ".gz" else raw)
