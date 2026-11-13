from fastapi.testclient import TestClient

from fieldshift.application.use_cases import plan_rotation as uc
from fieldshift.main import app

AS_OF = "2026-11-14"


def create_plan(client, coastal=False, **kwargs):
    field = client.post(
        "/v1/fields",
        json={
            "name": "Adaptive test",
            "lat": 10.03,
            "lon": 105.78,
            "profile": {"cache_key": "cantho", "coastal_salinity_risk": coastal},
        },
    ).json()
    response = client.post(
        "/v1/plans", json={"field_id": field["id"], "as_of": AS_OF, "horizon_seasons": 1, **kwargs}
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_status_threshold_units_timing_and_drainage():
    with TestClient(app) as client:
        p = create_plan(client, coastal=True)
        url = f"/v1/plans/{p['decision_id']}"
        assert client.get(url + "/status").json() == {
            "decision_id": p["decision_id"],
            "status": "OK",
            "fired": [],
        }
        trigger = p["baseline"]["triggers"][0]
        assert trigger["variable"] == "canal_ecw" and trigger["op"] == "gt"

        def observe(variable, date, **kwargs):
            response = client.post(
                f"/v1/fields/{p['field_id']}/observations",
                json={"variable": variable, "observed_at": date, **kwargs},
            )
            assert response.status_code == 201
            return response.json()["id"]

        observe("canal_ecw", AS_OF, value=10, unit="dS/m")
        observe("canal_ecw", "2026-11-15", value=10, unit="ppt")
        observe("canal_ecw", "2026-11-15", value=0, unit="dS/m")
        threshold = min(
            t["threshold"]
            for option in [p["baseline"], *p["options"]]
            for t in option["triggers"]
            if t["variable"] == "canal_ecw"
        )
        observe("canal_ecw", "2026-11-15", value=threshold, unit="dS/m")
        assert client.get(url + "/status").json()["status"] == "OK"
        ecw_id = observe("canal_ecw", "2026-11-16", value=10, unit="dS/m")
        drainage_id = observe("drainage", "2026-11-16", value_text="poor")
        status = client.get(url + "/status").json()
        assert status["status"] == "REPLAN_REQUIRED"
        assert {x["observation_id"] for x in status["fired"]} == {ecw_id, drainage_id}
        assert client.get(url).json() == p  # snapshot remains immutable
        assert client.get("/v1/plans/nonexistent/status").status_code == 404


def test_priorities_reuse_matches_full_run(monkeypatch):
    with TestClient(app) as client:
        parent = create_plan(client)
        priorities = ["soil_health", "minimal_change", "save_water"]
        full = client.post("/v1/plans", json={**parent["request"], "priorities": priorities}).json()

        def forbidden(*args, **kwargs):
            raise AssertionError("Priorities-only what-if must not load data or simulate")

        monkeypatch.setattr(uc, "run_plan", forbidden)
        monkeypatch.setattr(uc, "context_for", forbidden)
        monkeypatch.setattr(uc, "simulate_season", forbidden)
        result = client.post(
            f"/v1/plans/{parent['decision_id']}/what-if", json={"priorities": priorities}
        )
        assert result.status_code == 201, result.text
        reused = result.json()
        assert reused["options"] == full["options"]
        assert reused["baseline"] == full["baseline"]
        assert reused["computation"]["season_simulations"] == 0
        assert reused["parent_id"] == parent["decision_id"]
        empty_override = client.post(
            f"/v1/plans/{parent['decision_id']}/what-if",
            json={"priorities": priorities, "override": {}},
        ).json()
        assert empty_override["options"] == full["options"]
        assert empty_override["computation"]["season_simulations"] == 0
        option = reused["options"][0]
        twin = client.get(
            f"/v1/plans/{reused['decision_id']}/twin", params={"sequence_id": option["sequence_id"]}
        ).json()
        assert twin["series"]
        assert client.get(f"/v1/plans/{parent['decision_id']}").json() == parent


def test_hindcast_and_offline_fallback(monkeypatch):
    from fieldshift.application.use_cases import outlook_context

    with TestClient(app) as client:
        historical = create_plan(client, as_of="2026-11-01")
        assert not any(s["kind"] == "FORECAST" for s in historical["scenarios"])
        assert not next(g for g in historical["gates"] if g["gate"] == "G6")["passed"]
        assert historical["field_state"]["upstream_discharge"]["value"] is None
        monkeypatch.setattr(outlook_context, "load_seasonal", lambda *a: (None, "UNAVAILABLE"))
        monkeypatch.setattr(outlook_context, "load_projections", lambda *a: ([], []))
        offline = create_plan(client)
        assert {s["kind"] for s in offline["scenarios"]} == {"CLIMATOLOGY", "STRESS_TEST"}
        assert not next(g for g in offline["gates"] if g["gate"] == "G6")["passed"]


def test_g8_applied_before_package_persistence(monkeypatch):
    with TestClient(app) as client:
        monkeypatch.setattr(
            uc,
            "run_plan",
            lambda *a, **kw: {
                "gates": [],
                "baseline": {},
                "options": [
                    {
                        "metrics": {
                            "unverified": {"value": 12, "unit": "mm", "evidence_ids": ["missing"]}
                        }
                    }
                ],
                "trajectories": {},
            },
        )
        p = create_plan(client)
        number = p["options"][0]["metrics"]["unverified"]
        assert number["value"] is None and number["reason"] == "EVIDENCE_INCOMPLETE_G8"
        assert not p["gates"][0]["passed"]
        assert client.get(f"/v1/plans/{p['decision_id']}").json() == p
