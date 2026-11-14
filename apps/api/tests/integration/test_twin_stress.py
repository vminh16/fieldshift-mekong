"""Twin weekly stress uses the engine's water_stress_days definition (paddy pond-empty days count; bare fallow never)."""

from fastapi.testclient import TestClient

from fieldshift.domain.catalog import CROP_BY_ID
from fieldshift.main import app


def test_twin_stress_matches_engine_and_ignores_fallow():
    with TestClient(app) as client:
        p = client.post(
            "/v1/plans",
            json={
                "field_id": "fld_soctrang",
                "as_of": "2026-11-14",
                "constraints": {"irrigation": "canal_limited"},
            },
        ).json()
        base = p["baseline"]
        assert base["metrics"]["sc_dry"]["water_stress_days"]["value"] > 0
        for option in [base, *p["options"]]:
            twin = client.get(
                f"/v1/plans/{p['decision_id']}/twin",
                params={"sequence_id": option["sequence_id"], "scenario_id": "sc_dry"},
            ).json()
            for week in twin["series"]:
                if week["crop"] and CROP_BY_ID[week["crop"]]["water_regime"] == "none":
                    assert week["stress_risk"] == "LOW"
            if option is base:
                assert any(w["stress_risk"] != "LOW" for w in twin["series"])
