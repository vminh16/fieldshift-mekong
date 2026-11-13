"""Offline config shape checks; not a scientific-validation substitute."""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = [
    ROOT / "configs/regions/mekong.yaml",
    ROOT / "configs/crops/catalog.yaml",
    ROOT / "configs/rules/feasibility.yaml",
    ROOT / "configs/scenarios/defaults.yaml",
    ROOT / "data/catalog/sources.yaml",
]


def main() -> None:
    for path in CONFIGS:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Expected mapping at {path}")
        print(f"OK: {path.relative_to(ROOT)}")
    crops = yaml.safe_load((ROOT / "configs/crops/catalog.yaml").read_text())
    if not crops.get("crops") or any(
        item.get("approved_for_planning") is not False for item in crops["crops"]
    ):
        raise ValueError("Starter crop catalog must NOT imply approval")
    sample = json.loads((ROOT / "data/samples/sample_field.json").read_text())
    if sample["sample_type"] != "SYNTHETIC_DEMO_ONLY":
        raise ValueError("Sample must declare synthetic status")
    print("Config structure OK (domain calibration is NOT validated).")


if __name__ == "__main__":
    main()
