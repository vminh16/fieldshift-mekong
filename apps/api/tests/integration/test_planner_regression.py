"""Two-stage screening preserves the original fixture shortlist and every scenario's metrics."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fieldshift.domain.engines import rotation_planner as planner
from fieldshift.infrastructure.persistence import sqlite as db
from fieldshift.main import app

FIXTURES = Path(__file__).resolve().parents[4] / "contracts" / "fixtures"
# Captured before two-stage screening; fixture regeneration must never redefine the shortlist.
# One deliberate physics change since: the harvest-to-sowing fallow gap is now simulated (P1-3).
# In Can Tho the ~5-week dry-season gap after the Dong Xuan rice dries the bed before Xuan He
# peanut (sc_clim irrigation 1077 -> 1144 mm, stress p90 12 -> 13 d), so rice-peanut-rice
# becomes dominated by soybean-rice-rice and leaves the Pareto front; only 3 options remain.
EXPECTED_IDS = {
    "cantho": [
        "seq_soybean_rice_rice__early_standard_standard",
        "seq_mungbean_rice_rice__early_standard_standard",
        "seq_fallow_cover_rice_rice__early_standard_standard",
    ],
    "soctrang": [
        "seq_fallow_cover_rice_rice__early_standard_standard",
        "seq_mungbean_rice_rice__early_standard_standard",
        "seq_soybean_rice_rice__early_standard_standard",
    ],
}


@pytest.mark.parametrize("field", EXPECTED_IDS)
def test_fixture_picks_metrics_and_selected_only_details(field, monkeypatch, tmp_path):
    # Other integration tests add observations to the demo fields; fixture comparisons
    # need their original, unobserved state.
    settings = replace(db.get_settings(), db_path=tmp_path / "regression.db")
    monkeypatch.setattr(db, "get_settings", lambda: settings)
    expected = json.loads((FIXTURES / f"plan_{field}.json").read_text())
    evaluations, distributions, trajectories = [], [], []
    evaluate = planner.Evaluator.evaluate
    distribution = planner.distribution_view
    trajectory = planner.trajectory_members

    def tracked_evaluate(self, seq, scenario_ids=None):
        evaluations.append((seq["sequence_id"], scenario_ids))
        return evaluate(self, seq, scenario_ids)

    def tracked_distribution(*args):
        distributions.append(1)
        return distribution(*args)

    def tracked_trajectory(ev, candidate, scenario, end):
        trajectories.append((candidate["seq"]["sequence_id"], scenario["scenario_id"]))
        return trajectory(ev, candidate, scenario, end)

    monkeypatch.setattr(planner.Evaluator, "evaluate", tracked_evaluate)
    monkeypatch.setattr(planner, "distribution_view", tracked_distribution)
    monkeypatch.setattr(planner, "trajectory_members", tracked_trajectory)
    with TestClient(app) as client:
        response = client.post("/v1/plans", json=expected["request"])
        assert response.status_code == 201, response.text
        actual = response.json()

        assert [o["sequence_id"] for o in actual["options"]] == EXPECTED_IDS[field]
        assert [o["sequence_id"] for o in expected["options"]] == EXPECTED_IDS[field]
        for result, fixture in zip(
            [actual["baseline"], *actual["options"]], [expected["baseline"], *expected["options"]]
        ):
            for key in ("sequence_id", "metrics", "distribution", "delta_vs_baseline", "seasons"):
                assert result[key] == fixture[key], (result["sequence_id"], key)
        assert actual["excluded"] == expected["excluded"]
        for key in ("generated", "calendar_feasible", "evaluated_feasible", "pareto_front"):
            assert actual["stats"][key] == expected["stats"][key]

        chosen = [actual["baseline"]["sequence_id"], *EXPECTED_IDS[field]]
        assert [sid for sid, scenarios in evaluations if scenarios is None] == chosen
        screened = [scenarios for _, scenarios in evaluations if scenarios is not None]
        assert len(screened) == actual["stats"]["calendar_feasible"] + 1
        assert all(scenarios == {"sc_clim", "sc_dry"} for scenarios in screened)
        assert len(distributions) == len(chosen)
        assert set(trajectories) == {
            (sid, scenario["scenario_id"]) for sid in chosen for scenario in actual["scenarios"]
        }
        timings = actual["stats"]["timings_ms"]
        assert all(value >= 0 for value in timings.values())
        assert timings["total"] == pytest.approx(
            sum(value for key, value in timings.items() if key != "total"), abs=0.1
        )
        if field == "cantho":
            assert "~7.990 m³/ha" in actual["options"][1]["summary_vi"]
        else:
            conditions = [
                t["condition"]
                for option in [actual["baseline"], *actual["options"]]
                for t in option["triggers"]
            ]
            assert any("3,33 dS/m" in condition for condition in conditions)
            assert any("1,3 ‰" in condition for condition in conditions)
