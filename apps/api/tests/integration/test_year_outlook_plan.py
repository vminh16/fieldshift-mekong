"""ENSO analog years: present for an El Niño as_of; absent (engine unchanged) without ONI."""

import datetime as dt
import json

from fastapi.testclient import TestClient

from fieldshift.application.use_cases.plan_rotation import context_for
from fieldshift.domain.engines import rotation_planner as planner
from fieldshift.domain.engines.field_state import estimate_state
from fieldshift.infrastructure.crop_models.fao56_water import simulate_season
from fieldshift.infrastructure.persistence import sqlite as db
from fieldshift.main import app

AS_OF = "2026-11-14"


def test_el_nino_plan_has_analog_scenario_outlook_and_twin():
    with TestClient(app) as client:
        r = client.post("/v1/plans", json={"field_id": "fld_soctrang", "as_of": AS_OF})
        assert r.status_code == 201, r.text
        plan = r.json()
        yo = plan["year_outlook"]
        assert yo["status"] == "OK" and yo["scenario_id"] == "sc_enso_analog"
        assert yo["enso"]["centered_month"] == "2026-09" and yo["enso"]["phase"] == "EL_NINO_STRONG"
        assert 3 <= len(yo["analog_years"]) <= 5 and 2015 in yo["analog_years"]
        assert all(y < 2026 for y in yo["analog_years"])
        assert yo["analog_labels_vi"][0] == "2015–16"
        assert yo["dry_season_rain"]["ratio"] < 1 and yo["skill"]["correlation_r"] < 0
        assert yo["skill"]["n_years"] >= 20 and "không phải dự báo" in yo["skill"]["note_vi"]
        assert all(e in plan["evidence"] for e in yo["evidence_ids"])
        sc = next(s for s in plan["scenarios"] if s["scenario_id"] == "sc_enso_analog")
        assert sc["kind"] == "CLIMATOLOGY" and sc["probability"] is None
        assert sc["probability_semantics"] == "ANALOG_YEARS_CONDITIONED_ON_ENSO_NOT_FORECAST"
        assert [m["year"] for m in sc["members"]] == yo["analog_years"]
        assert next(g for g in plan["gates"] if g["gate"] == "G8")["passed"]
        for option in [plan["baseline"], *plan["options"]]:
            assert option["metrics"]["sc_enso_analog"]["irrigation_need"]["value"] is not None
            twin = client.get(
                f"/v1/plans/{plan['decision_id']}/twin",
                params={"sequence_id": option["sequence_id"], "scenario_id": "sc_enso_analog"},
            )
            assert twin.status_code == 200, twin.text
            assert {m["year"] for m in twin.json()["members"]} == set(yo["analog_years"])


def test_without_oni_engine_output_is_unchanged(monkeypatch):
    with TestClient(app):
        field = db.get(db.connect(), "fields", "fld_cantho")
    as_of = dt.date.fromisoformat(AS_OF)
    ctx = context_for(field, as_of)
    state = estimate_state(field, ctx, as_of, [])
    req = {"as_of": AS_OF, "horizon_seasons": 3}
    screened = []
    evaluate = planner.Evaluator.evaluate

    def tracked(self, seq, scenario_ids=None):
        if scenario_ids is not None:
            screened.append(frozenset(scenario_ids))
        return evaluate(self, seq, scenario_ids)

    monkeypatch.setattr(planner.Evaluator, "evaluate", tracked)

    def run(c):
        out = planner.run_plan(field, c, state, req, simulate=simulate_season)
        out["stats"].pop("timings_ms")
        return out

    # Today's engine never read these keys; ONI missing at as_of must behave the same.
    legacy = run({k: v for k, v in ctx.items() if k not in ("enso", "imerg_monthly")})
    missing = run({**ctx, "enso": {**ctx["enso"], "latest": None}})
    assert missing.pop("year_outlook")["status"] == "UNAVAILABLE"
    legacy.pop("year_outlook")
    assert json.dumps(missing, default=str) == json.dumps(legacy, default=str)
    assert "sc_enso_analog" not in {s["scenario_id"] for s in missing["scenarios"]}
    assert set(screened) == {planner.SCREENING_SCENARIOS}
