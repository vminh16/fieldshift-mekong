"""The simulation UI uses paired members and real water-balance outputs, offline."""

import datetime as dt
import statistics

import pytest
from fastapi.testclient import TestClient

from fieldshift.application.use_cases import plan_rotation as uc
from fieldshift.domain.catalog import CROP_BY_ID
from fieldshift.domain.engines.future_outlook import dry_season_rain
from fieldshift.infrastructure.persistence import sqlite as db
from fieldshift.main import app


@pytest.fixture
def simulation_plan(monkeypatch, offline_outlook):
    calls = 0
    simulate = uc.simulate_season

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return simulate(*args, **kwargs)

    monkeypatch.setattr(uc, "simulate_season", counted)
    # The source adapters are forced offline by conftest for every test.
    with TestClient(app) as client:
        response = client.post("/v1/plans", json={"field_id": "fld_cantho", "as_of": "2026-11-14"})
        assert response.status_code == 201, response.text
        plan = response.json()
        assert plan["stats"]["season_simulations"] == calls
        yield client, plan


def test_distribution_matches_metrics(simulation_plan):
    _, plan = simulation_plan
    kinds = {s["scenario_id"]: s["kind"] for s in plan["scenarios"]}
    assert "member_trajectories" not in plan and "trajectories" not in plan
    for option in [plan["baseline"], *plan["options"]]:
        assert set(option["distribution"]) == set(kinds)
        dist = option["distribution"]["sc_clim"]
        assert (
            statistics.median(d["irrigation_mm"] for d in dist)
            == option["metrics"]["sc_clim"]["irrigation_need"]["value"]
        )
        assert (
            statistics.median(d["water_stress_days"] for d in dist)
            == option["metrics"]["sc_clim"]["water_stress_days"]["value"]
        )
        assert (
            statistics.median(d["heat_stress_days"] for d in dist)
            == option["metrics"]["sc_clim"]["heat_stress_days_sensitive_stage"]["value"]
        )
        for sid, dist in option["distribution"].items():
            assert len(dist) == option["metrics"][sid]["years_used"]
            for i, dot in enumerate(dist):
                assert dot["member"] == i
                for key in ("irrigation_mm", "water_stress_days", "heat_stress_days"):
                    assert type(dot[key]) is int and dot[key] >= 0
                if kinds[sid] == "FORECAST":
                    assert dot["year"] is None and dot["member_label"]
                else:
                    assert type(dot["year"]) is int and "member_label" not in dot
    for option in plan["options"]:
        assert option["reasons"][0]["text"].rstrip(".") in option["summary_vi"]
        assert all(
            s["crop_name_vi"] in option["summary_vi"]
            for s, b in zip(option["seasons"], plan["baseline"]["seasons"])
            if s["crop"] != b["crop"]
        )


def test_twin_compare_same_member_year_dates_without_simulating(simulation_plan, monkeypatch):
    client, plan = simulation_plan

    def unexpected(*args, **kwargs):
        pytest.fail("Twin must only read the immutable decision, without loading data/simulating")

    monkeypatch.setattr(uc, "simulate_season", unexpected)
    monkeypatch.setattr(uc, "context_for", unexpected)
    for sid in ("sc_clim", "sc_forecast", "sc_proj_ACCESS-CM2_ssp245"):
        for option in plan["options"]:
            params = {"sequence_id": option["sequence_id"], "scenario_id": sid}
            url = f"/v1/plans/{plan['decision_id']}"
            default = client.get(url + "/twin-compare", params=params)
            assert default.status_code == 200, default.text
            pair = default.json()
            dist = option["distribution"][sid]
            median_member = sorted(dist, key=lambda d: (d["irrigation_mm"], d["member"]))[
                len(dist) // 2
            ]["member"]
            assert pair["option"]["member"] == median_member
            for member in (median_member, 0, len(dist) - 1):
                params["member"] = member
                response = client.get(url + "/twin-compare", params=params)
                assert response.status_code == 200, response.text
                pair = response.json()
                baseline, twin = pair["baseline"], pair["option"]
                assert baseline["member"] == twin["member"] == member
                assert baseline["analog_year"] == twin["analog_year"] == dist[member]["year"]
                assert [r["date"] for r in baseline["series"]] == [
                    r["date"] for r in twin["series"]
                ]
                single = client.get(url + "/twin", params=params).json()
                assert single["member"] == member and single["analog_year"] == twin["analog_year"]
                for season in option["seasons"]:
                    rows = [r for r in single["series"] if r["season_index"] == season["index"]]
                    assert rows[0]["date"] == season["sow"]
                    assert rows[-1]["irrigation_cum"]["value"] == pytest.approx(
                        sum(r["irrigation_week"]["value"] for r in rows), abs=1
                    )
                assert twin["series"][-1]["irrigation_cum"]["value"] == pytest.approx(
                    dist[member]["irrigation_mm"], abs=1
                )
                if sid == "sc_forecast":
                    assert baseline["member_label"] == twin["member_label"]
            assert client.get(url + "/twin", params={**params, "member": -1}).status_code == 422
            assert (
                client.get(
                    url + "/twin-compare", params={**params, "member": len(dist)}
                ).status_code
                == 404
            )
    assert (
        client.get(url + "/twin-compare", params={**params, "scenario_id": "missing"}).status_code
        == 404
    )
    assert client.get(url + "/twin", params={**params, "sequence_id": "missing"}).status_code == 404


def test_twin_water_events_and_rainfall_labels(simulation_plan):
    client, plan = simulation_plan
    context = uc.context_for(
        db.get(db.connect(), "fields", plan["field_id"]),
        dt.date.fromisoformat(plan["as_of"]),
    )
    for option in [plan["baseline"], *plan["options"]]:
        response = client.get(
            f"/v1/plans/{plan['decision_id']}/twin",
            params={"sequence_id": option["sequence_id"]},
        )
        assert response.status_code == 200, response.text
        twin = response.json()
        dry_order = sorted(
            twin["members"],
            key=lambda m: (dry_season_rain(context, None, m["year"]), m["member"]),
        )
        assert dry_order[0]["label_vi"].startswith("Năm hạn")
        assert dry_order[-1]["label_vi"].startswith("Năm ướt")
        assert dry_order[len(dry_order) // 2]["label_vi"] == "Năm bình thường"
        if option["is_baseline"]:
            url = f"/v1/plans/{plan['decision_id']}/twin"
            params = {"sequence_id": option["sequence_id"]}
            wet = client.get(url, params={**params, "scenario_id": "sc_wet_ref"}).json()
            assert wet["members"][0]["label_vi"].startswith("Năm ướt")
            dry = client.get(url, params={**params, "scenario_id": "sc_dry"}).json()
            assert not any(m["label_vi"].startswith("Năm ướt") for m in dry["members"])
        assert len(twin["members"]) == len(option["distribution"]["sc_clim"])
        for season in option["seasons"]:
            for kind in ("sow", "harvest"):
                assert {
                    "date": season[kind],
                    "type": kind,
                    "season_index": season["index"],
                    "crop": season["crop"],
                } in twin["events"]
        assert {event["type"] for event in twin["events"]} == {
            "sow",
            "harvest",
            "salinity_season_start",
            "salinity_season_end",
        }
        for row in twin["series"]:
            assert row["rain_week"]["value"] >= 0 and row["irrigation_week"]["value"] >= 0
            assert row["rain_week"]["evidence_ids"]
            if row["crop"] is None:
                assert row["root_zone_water"]["value"] is None
                continue
            crop = CROP_BY_ID[row["crop"]]
            if crop["water_regime"] == "paddy":
                assert row["ponding_mm"]["value"] >= 0
            else:
                assert row["ponding_mm"]["value"] is None
                assert row["ponding_mm"]["reason"] == "NOT_PADDY"
            assert (
                crop["root_depth_m"]["min"]
                <= row["root_depth_m"]["value"]
                <= crop["root_depth_m"]["max"]
            )
