"""Generate/check the single transport schema from FastAPI app."""

import argparse
import json
from pathlib import Path

from fieldshift.main import app

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/openapi.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.check:
        if not CONTRACT.is_file() or CONTRACT.read_text(encoding="utf-8") != generated:
            raise SystemExit("OpenAPI mismatch. Run 'make contracts' and commit generated file.")
        print("OpenAPI contract is up-to-date")
    else:
        CONTRACT.write_text(generated, encoding="utf-8")
        print(f"Wrote {CONTRACT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
