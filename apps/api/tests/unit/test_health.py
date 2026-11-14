from fastapi.testclient import TestClient

from fieldshift.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "mvp"


def test_plan_requires_known_field() -> None:
    with TestClient(app) as client:
        response = client.post("/v1/plans", json={"field_id": "fld_missing", "as_of": "2026-11-14"})
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "FIELD_NOT_FOUND"


def test_sources_inventory_matches_all_demo_evidence_fixtures():
    import json
    from pathlib import Path

    with TestClient(app) as client:
        inventory = client.get("/v1/sources").json()
    rows = inventory["sources"]
    ids = {s["id"] for s in rows}
    assert len(ids) == len(rows)
    order = {name: i for i, name in enumerate(("DECISION", "EVIDENCE", "CONTEXT", "NOT_USED"))}
    assert [order[s["use"]] for s in rows] == sorted(order[s["use"]] for s in rows)
    for site in ("cantho", "soctrang", "bentre", "chaudoc"):
        fixture = Path(__file__).resolve().parents[4] / "contracts/fixtures" / f"plan_{site}.json"
        plan = json.loads(fixture.read_text())
        assert set(plan["evidence"]) <= ids
