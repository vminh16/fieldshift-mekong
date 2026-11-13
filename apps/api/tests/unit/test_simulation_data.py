"""Rounding, weekly aggregation and immutable-snapshot compatibility for Twin."""

import statistics

import pytest

from fieldshift.application.errors import NotFound
from fieldshift.application.use_cases.plan_rotation import twin_compare, twin_slice
from fieldshift.domain.engines.rotation_planner import distribution_view, weekly_water


@pytest.mark.parametrize(
    "totals",
    ([1746.2, 1746.9], [0, 0, 1.3, 1.4], [0], [0, 0, 0], [125.4, 150.9, 500], [1.1, 2.9]),
)
def test_integer_distribution_retains_p50_and_member_values(totals):
    scenarios = {
        "sc_clim": {
            "kind": "CLIMATOLOGY",
            "members": [{"year": 2001 + i} for i in range(len(totals))],
        }
    }
    runs = [
        [{"irrigation_mm": total, "water_stress_days": i, "heat_stress_days_sensitive": i + 1}]
        for i, total in enumerate(totals)
    ]
    p50 = round(statistics.median(totals))
    dots = distribution_view(
        {"sc_clim": runs}, scenarios, {"sc_clim": {"irrigation_mm": {"p50": p50}}}
    )["sc_clim"]
    assert statistics.median(d["irrigation_mm"] for d in dots) == p50
    for i, (dot, total) in enumerate(zip(dots, totals)):
        assert dot["member"] == i and dot["year"] == 2001 + i
        assert type(dot["irrigation_mm"]) is int and dot["irrigation_mm"] >= 0
        assert abs(dot["irrigation_mm"] - total) <= 1
        assert dot["water_stress_days"] == i and dot["heat_stress_days"] == i + 1


def test_weekly_ponding_is_mean_not_last_day():
    rows = [
        {
            "date": f"2026-12-0{i + 1}",
            "stage": "initial",
            "root_depth_m": 0.3 + i * 0.02,
            "water_frac": 0.5,
            "ponding_mm": depth,
            "rain": 2,
            "irrigation": 3,
            "ks": 1,
        }
        for i, depth in enumerate((0, 25, 50, 75, 100))
    ]
    week = weekly_water(rows)
    assert week["ponding_mm"] == 50
    assert week["root_depth_m"] == 0.3
    assert week["irrigation_week"] == 15 and week["rain_week"] == 10
    for row in rows:
        row["ponding_mm"] = None
    assert weekly_water(rows)["ponding_mm"] is None


def test_old_snapshot_keeps_default_twin_without_inventing_members():
    original = {"analog_year": 2015, "step": "week", "series": []}
    package = {
        "decision_id": "old",
        "baseline": {"sequence_id": "base"},
        "trajectories": {"seq": {"sc_clim": original}},
    }
    assert twin_slice(package, "seq", "sc_clim") == {
        "decision_id": "old",
        "sequence_id": "seq",
        "scenario_id": "sc_clim",
        **original,
    }
    for action in (twin_compare, twin_slice):
        with pytest.raises(NotFound, match="member"):
            action(package, "seq", "sc_clim", 0)
    assert package["trajectories"]["seq"]["sc_clim"] == original
