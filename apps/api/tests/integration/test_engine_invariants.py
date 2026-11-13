"""Invariant tests from design v2 §14 (AC-01..AC-10). Uses cached NASA POWER data; runs offline."""

from fastapi.testclient import TestClient

from fieldshift.main import app

AS_OF = "2026-11-14"


def plan(c, field_id, **kw):
    r = c.post("/v1/plans", json={"field_id": field_id, "as_of": AS_OF, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def all_options(p):
    return [p["baseline"], *p["options"]]


def test_core_invariants():
    with TestClient(app) as c:
        inland = plan(c, "fld_cantho")
        coastal = plan(c, "fld_soctrang")

        for p in (inland, coastal):
            assert (
                p["baseline"]["is_baseline"] and p["baseline"]["seasons"]
            )  # baseline always present
            assert len(p["options"]) >= 2 or p["notes"]  # AC-01
            assert all(
                s["kind"] in ("CLIMATOLOGY", "STRESS_TEST") for s in p["scenarios"]
            )  # AC-03: no fake forecast
            assert all(s["probability"] is None for s in p["scenarios"])
            for o in p["options"]:
                assert o["decision_status"] != "NOT_FEASIBLE"
                assert o["metrics"]["sc_clim"]["yield"]["value"] is None  # G7: no invented yield
                assert o["soil_benefit"]["claim_type"] == "POTENTIAL_QUALITATIVE"  # AC-08
                assert "sc_clim" in o["delta_vs_baseline"]  # same scenario as baseline
                if any(r["severity"] == "UNKNOWN_REQUIRES_CHECK" for r in o["rules"]):
                    assert o["decision_status"] == "CONDITIONAL_PENDING_CHECK"
            assert all(r["severity"] == "HARD" for r in p["excluded"])

        # AC-02: coastal + unknown ECw -> never "safe"; salinity unknown in state
        assert coastal["field_state"]["canal_ecw"]["value"] is None
        assert any(g["gate"] == "G5" and not g["passed"] for g in coastal["gates"])
        assert not any(g["gate"] == "G5" for g in inland["gates"])
        rice_coastal = coastal["baseline"]
        assert rice_coastal["decision_status"] == "CONDITIONAL_PENDING_CHECK"

        # AC-04: no data after as_of
        assert inland["field_state"]["data_last_date"] < AS_OF

        # AC-09: twin = slice of the same package
        o = inland["options"][0]
        t = c.get(
            f"/v1/plans/{inland['decision_id']}/twin",
            params={"sequence_id": o["sequence_id"], "scenario_id": "sc_clim"},
        ).json()
        assert t["series"] and t["series"][0]["season_index"] == 1

        # Measured ECw changes the coastal salinity status (PS-02)
        r = c.post(
            "/v1/fields/fld_soctrang/observations",
            json={
                "variable": "canal_ecw",
                "value": 0.5,
                "unit": "dS/m",
                "observed_at": "2026-11-10",
                "evidence_kind": "OBSERVED_FIELD",
            },
        )
        assert r.status_code == 201
        coastal2 = plan(c, "fld_soctrang")
        assert coastal2["field_state"]["canal_ecw"]["value"] == 0.5
        assert not any(
            r["rule_id"] == "R_SALINITY_UNKNOWN" for o in all_options(coastal2) for r in o["rules"]
        )

        # what-if creates a new decision, parent untouched
        w = c.post(
            f"/v1/plans/{inland['decision_id']}/what-if",
            json={"override": {"rain_delta_pct": -40, "temp_delta_c": 2}},
        )
        assert w.status_code == 201 and w.json()["parent_id"] == inland["decision_id"]
        assert any(s["scenario_id"] == "sc_whatif" for s in w.json()["scenarios"])
        assert (
            c.get(f"/v1/plans/{inland['decision_id']}").json()["generated_at"]
            == inland["generated_at"]
        )

        # AC-10: replan keeps history and plans only remaining seasons
        rp = c.post(
            f"/v1/plans/{inland['decision_id']}/replan",
            json={
                "as_of": "2027-03-20",
                "completed": [{"crop": "rice", "sow": "2026-12-08", "harvest": "2027-03-17"}],
            },
        )
        assert rp.status_code == 201, rp.text
        assert (
            len(rp.json()["baseline"]["seasons"]) == 2 and rp.json()["history"][0]["crop"] == "rice"
        )


def test_poor_drainage_excludes_upland():  # UC-02
    with TestClient(app) as c:
        c.patch("/v1/fields/fld_chaudoc", json={"profile": {"drainage": "poor"}})
        p = plan(c, "fld_chaudoc")
        for o in p["options"]:
            assert all(s["crop"] in ("rice", "fallow_cover") for s in o["seasons"]), o["seasons"]
