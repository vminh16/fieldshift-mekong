"""Regenerate planning, Twin, comparison and context fixtures from a local API (port 8095)."""

import argparse
import json
from pathlib import Path

import httpx

FIXTURES = Path(__file__).resolve().parents[1] / "contracts" / "fixtures"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8095/v1")
    parser.add_argument("--as-of", default="2026-11-14")
    args = parser.parse_args()

    def save(name, response):
        response.raise_for_status()
        data = response.json()
        (FIXTURES / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"OK: contracts/fixtures/{name}", flush=True)
        return data

    with httpx.Client(base_url=args.base_url + "/", timeout=180) as client:
        save("sources.json", client.get("sources"))
        for site in ("bentre", "chaudoc"):
            save(
                f"plan_{site}.json",
                client.post("plans", json={"field_id": f"fld_{site}", "as_of": args.as_of}),
            )
        inland = save(
            "plan_cantho.json",
            client.post("plans", json={"field_id": "fld_cantho", "as_of": args.as_of}),
        )
        save(
            "plan_soctrang.json",
            client.post("plans", json={"field_id": "fld_soctrang", "as_of": args.as_of}),
        )
        save(
            "twin_cantho.json",
            client.get(
                f"plans/{inland['decision_id']}/twin",
                params={
                    "sequence_id": inland["options"][0]["sequence_id"],
                    "scenario_id": "sc_clim",
                },
            ),
        )
        save(
            "twin_compare_cantho.json",
            client.get(
                f"plans/{inland['decision_id']}/twin-compare",
                params={
                    "sequence_id": inland["options"][0]["sequence_id"],
                    "scenario_id": "sc_clim",
                },
            ),
        )
        save(
            "context_cantho.json",
            client.get("fields/fld_cantho/context", params={"as_of": args.as_of}),
        )


if __name__ == "__main__":
    main()
