from fastapi.testclient import TestClient
from fieldshift.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "scaffold"


def test_planning_not_falsely_implemented() -> None:
    response = client.post("/v1/plans")
    assert response.status_code == 501
