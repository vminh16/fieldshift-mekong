"""Versioned crop catalog and region profiles (configuration, not code). Files live in fieldshift/resources."""

import json
from pathlib import Path

RESOURCES = Path(__file__).resolve().parents[1] / "resources"

CROPS = json.loads((RESOURCES / "crops.json").read_text(encoding="utf-8"))
REGIONS = {
    r["id"]: r
    for r in json.loads((RESOURCES / "regions.json").read_text(encoding="utf-8"))["regions"]
}
CROP_BY_ID = {c["id"]: c for c in CROPS["crops"]}
