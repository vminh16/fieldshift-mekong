from fastapi.testclient import TestClient

from fieldshift.main import app

AS_OF = "2026-11-14"


def plan(client):
    field = client.post(
        "/v1/fields",
        json={
            "name": "Chain test",
            "lat": 10.03,
            "lon": 105.78,
            "profile": {"cache_key": "cantho"},
        },
    ).json()
    r = client.post(
        "/v1/plans", json={"field_id": field["id"], "as_of": AS_OF, "horizon_seasons": 3}
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_user_chain_is_simulated_as_a_child_without_touching_the_parent():
    with TestClient(app) as client:
        parent = plan(client)
        r = client.post(
            f"/v1/plans/{parent['decision_id']}/evaluate",
            json={"crops": ["mungbean", "rice", "rice"]},
        )
        assert r.status_code == 201, r.text
        child = r.json()
        assert child["kind"] == "WHAT_IF" and child["parent_id"] == parent["decision_id"]
        assert child["request"]["evaluate_chain"] == ["mungbean", "rice", "rice"]
        assert [s["crop"] for s in child["baseline"]["seasons"]] == ["mungbean", "rice", "rice"]
        # Same scenarios as the parent, so twins line up member by member.
        assert [s["scenario_id"] for s in child["scenarios"]] == [
            s["scenario_id"] for s in parent["scenarios"]
        ]

        twin = client.get(
            f"/v1/plans/{child['decision_id']}/twin",
            params={
                "sequence_id": child["baseline"]["sequence_id"],
                "scenario_id": "sc_clim",
                "member": 3,
            },
        )
        assert twin.status_code == 200, twin.text
        assert twin.json()["member"] == 3 and twin.json()["series"]

        again = client.get(f"/v1/plans/{parent['decision_id']}").json()
        assert again["baseline"]["sequence_id"] == parent["baseline"]["sequence_id"]


def test_infeasible_chain_comes_back_with_its_hard_rules():
    with TestClient(app) as client:
        parent = plan(client)
        r = client.post(
            f"/v1/plans/{parent['decision_id']}/evaluate",
            json={"crops": ["watermelon", "watermelon", "watermelon"]},
        )
        assert r.status_code == 201, r.text
        base = r.json()["baseline"]
        if base["decision_status"] == "NOT_FEASIBLE":
            assert any(rule["severity"] == "HARD" for rule in base["rules"])


def test_chain_length_must_match_the_horizon():
    with TestClient(app) as client:
        parent = plan(client)
        r = client.post(
            f"/v1/plans/{parent['decision_id']}/evaluate", json={"crops": ["rice", "rice"]}
        )
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "CHAIN_LENGTH_MISMATCH"
        bad = client.post(
            f"/v1/plans/{parent['decision_id']}/evaluate", json={"crops": ["rice", "rice", "kale"]}
        )
        assert bad.status_code == 422


def test_engine_option_rerun_keeps_its_sow_timing_and_user_assumptions():
    with TestClient(app) as client:
        parent = plan(client)
        option = parent["options"][0]
        r = client.post(
            f"/v1/plans/{parent['decision_id']}/evaluate",
            json={
                "crops": [s["crop"] for s in option["seasons"]],
                "sow_timing": [s["sow_timing"] for s in option["seasons"]],
                "override": {"rain_delta_pct": -30, "salinity_onset_shift_weeks": -4},
            },
        )
        assert r.status_code == 201, r.text
        child = r.json()
        # Same chain and timing as the engine option, now under the user's assumptions.
        assert child["baseline"]["sequence_id"] == option["sequence_id"]
        assert child["override"]["rain_delta_pct"] == -30
        whatif = next(s for s in child["scenarios"] if s["scenario_id"] == "sc_whatif")
        assert whatif["origin"] == "user_what_if" and whatif["probability"] is None
        twin = client.get(
            f"/v1/plans/{child['decision_id']}/twin",
            params={"sequence_id": option["sequence_id"], "scenario_id": "sc_whatif", "member": 0},
        )
        assert twin.status_code == 200, twin.text
        assert client.get(f"/v1/plans/{parent['decision_id']}").json()["override"] is None


def test_sow_timing_must_match_the_chain():
    with TestClient(app) as client:
        parent = plan(client)
        r = client.post(
            f"/v1/plans/{parent['decision_id']}/evaluate",
            json={"crops": ["rice", "rice", "rice"], "sow_timing": ["early"]},
        )
        assert r.status_code == 422
