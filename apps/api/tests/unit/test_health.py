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
