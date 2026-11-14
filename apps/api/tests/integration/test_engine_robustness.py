"""Scenario labels, robustness/confidence, fallow-gap carry-over (AC-05), beam search, AC-06."""

import datetime as dt
import random
import time
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from fieldshift.application.use_cases import plan_rotation as uc
from fieldshift.domain.engines import rotation_planner as planner
from fieldshift.domain.engines.field_state import estimate_state
from fieldshift.infrastructure.persistence import sqlite as db
from fieldshift.main import app

AS_OF = "2026-11-14"
PRESENTATION = {
    "CLIMATOLOGY": ("inferred_by_model", "Dự kiến"),
    "FORECAST": ("forecast", "Dự báo mùa"),
    "CLIMATE_PROJECTION": ("climate_projection", "Khí hậu tương lai CMIP6"),
    "STRESS_TEST": ("assumed_scenario", "Kịch bản thử thách"),
}


@pytest.fixture
def client(monkeypatch, tmp_path):
    # Demo fields in their original, unobserved state (other tests add observations).
    settings = replace(db.get_settings(), db_path=tmp_path / "robustness.db")
    monkeypatch.setattr(db, "get_settings", lambda: settings)
    with TestClient(app) as c:
        yield c


def plan(c, field_id, **kw):
    r = c.post("/v1/plans", json={"field_id": field_id, "as_of": AS_OF, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def test_scenario_labels_robustness_and_confidence(client):
    p = plan(client, "fld_cantho")
    kinds = {s["scenario_id"]: s["kind"] for s in p["scenarios"]}
    assert {"FORECAST", "CLIMATE_PROJECTION", "STRESS_TEST"} <= set(kinds.values())
    option = p["options"][0]
    for sid, kind in kinds.items():
        origin, label = PRESENTATION[kind]
        need = option["metrics"][sid]["irrigation_need"]
        assert (need["origin"], need["label"]) == (origin, label), sid
        assert option["delta_vs_baseline"][sid]["irrigation_need"]["origin"] == origin
    for sid in ["sc_dry", "sc_forecast", *[s for s in kinds if s.startswith("sc_proj_")]]:
        twin = client.get(
            f"/v1/plans/{p['decision_id']}/twin",
            params={"sequence_id": option["sequence_id"], "scenario_id": sid},
        ).json()
        week = twin["series"][0]
        assert (
            week["irrigation_week"]["origin"],
            week["irrigation_week"]["label"],
        ) == PRESENTATION[kinds[sid]], sid

    base = p["baseline"]
    assert base["robustness"] is None and base["confidence"]["robust_scenarios"] == "n/a"
    for o in p["options"]:
        rob, conf = o["robustness"], o["confidence"]
        assert rob["total"] == len(kinds) and rob["rule"]
        lost = []
        for sid in kinds:
            m, b = o["metrics"][sid], base["metrics"][sid]
            stress = round(
                m["water_stress_days"]["value"] + m["heat_stress_days_sensitive_stage"]["value"], 1
            )
            stress_b = round(
                b["water_stress_days"]["value"] + b["heat_stress_days_sensitive_stage"]["value"], 1
            )
            if not (
                m["irrigation_need"]["value"] < b["irrigation_need"]["value"] and stress <= stress_b
            ):
                lost.append(sid)
        assert rob["lost_scenarios"] == lost and rob["wins"] == len(kinds) - len(lost)
        assert conf["robust_scenarios"] == f"{rob['wins']}/{rob['total']}"
        outlook_lost = [sid for sid in lost if kinds[sid] in ("FORECAST", "CLIMATE_PROJECTION")]
        reversal = [r for r in o["risks"] if r["code"] == "R_OUTLOOK_REVERSAL"]
        assert len(reversal) == len(outlook_lost)
        ratio = rob["wins"] / rob["total"]
        if (
            outlook_lost
            or conf["unknowns"]
            or o["decision_status"] != "RECOMMEND_FOR_CONSIDERATION"
        ):
            assert conf["level"] != "HIGH"
        expected = (
            "HIGH"
            if ratio >= 0.9
            and not conf["unknowns"]
            and not outlook_lost
            and o["decision_status"] == "RECOMMEND_FOR_CONSIDERATION"
            else "MEDIUM"
            if ratio >= 0.6
            else "LOW"
        )
        assert conf["level"] == expected
        if any(r["rule_id"] == "R_DRAINAGE_UNKNOWN" for r in o["rules"]):
            assert "drainage" in conf["unknowns"]
    assert next(g for g in p["gates"] if g["gate"] == "G8")["passed"]


def test_thresholds_are_read_at_call_time(client, monkeypatch):
    monkeypatch.setattr(planner, "HEAT_STRESS_DAYS_SOFT", 0)
    p = plan(client, "fld_cantho")
    for s in p["baseline"]["seasons"]:
        assert any(
            r["rule_id"] == "R_HEAT" and r["season_index"] == s["index"]
            for r in p["baseline"]["rules"]
        )


def evaluator(client, recorded):
    con = db.connect()
    field = uc.must(con, "fields", "fld_cantho", "FIELD_NOT_FOUND")
    as_of = dt.date.fromisoformat(AS_OF)
    ctx = uc.context_for(field, as_of)
    state = estimate_state(field, ctx, as_of, [])

    def simulate(weather, crop, sow, *args):
        recorded.append((crop["id"], sow, args[4]))
        return uc.simulate_season(weather, crop, sow, *args)

    return planner.Evaluator(ctx, state, field, as_of, 400, None, simulate=simulate), ctx


def test_ac05_order_changes_carryover_and_gap_mass_balance(client):
    recorded = []
    ev, ctx = evaluator(client, recorded)
    windows = planner.window_instances(ctx["region"], ev.as_of, 3)
    sows = [planner.sow_options(w)[i > 0] for i, w in enumerate(windows)]  # early, std, std
    a = planner.make_sequence(windows, ["rice", "peanut", "rice"], sows)
    b = planner.make_sequence(windows, ["peanut", "rice", "rice"], sows)
    key = ("sc_clim", 0)

    def incoming(seq):
        recorded.clear()
        result = ev.run(seq, key)
        crops = {s["crop"] for s in seq["seasons"]}
        deps = {(c, s): d for c, s, d in recorded if c in crops}
        return [deps.get((s["crop"], s["sow"])) for s in seq["seasons"]], result

    ev.memo.clear()
    deps_a, res_a = incoming(a)
    ev.memo.clear()
    deps_b, res_b = incoming(b)
    assert deps_a != deps_b  # same crop multiset, different order -> different carry-over
    assert [r["irrigation_mm"] for r in res_a] != [r["irrigation_mm"] for r in res_b]
    # A drained paddy (depletion 0) dries during the dry-season gap before peanut.
    assert deps_a[1] > res_a[0]["end_state"]["depletion_frac"]

    start = a["seasons"][0]["harvest"] + dt.timedelta(days=1)
    assert ev.fallow_gap(start, start, key, 0.0) is None  # zero-length gap is a no-op
    gap = ev.fallow_gap(start, a["seasons"][1]["sow"], key, 0.2)
    daily = gap["daily"]
    assert len(daily) == (a["seasons"][1]["sow"] - start).days and gap["irrigation_mm"] == 0
    # Bucket mass balance: Dr_end = Dr_0 + ET - rain + drainage above field capacity.
    balance = (
        0.2 * daily[0]["taw_mm"] + gap["etc_mm"] - gap["rain_mm"] + gap["runoff_or_deep_perc_mm"]
    )
    assert daily[-1]["depletion_mm"] == pytest.approx(balance, abs=0.5)
    assert gap["end_state"]["depletion_frac"] * daily[-1]["taw_mm"] == pytest.approx(
        daily[-1]["depletion_mm"], abs=0.1
    )


def reference_pareto(cands):
    keys = ["irr", "irr_dry", "stress_p90", "salt", "soil", "changes", "idle"]
    return [
        a
        for a in cands
        if not any(
            all(b["crit"][k] <= a["crit"][k] for k in keys)
            and any(b["crit"][k] < a["crit"][k] for k in keys)
            for b in cands
            if b is not a
        )
    ]


def test_fast_pareto_matches_quadratic_reference(client, monkeypatch):
    rng = random.Random(7)
    keys = ["irr", "irr_dry", "stress_p90", "salt", "soil", "changes", "idle"]
    for _ in range(50):
        cands = [{"crit": {k: rng.randint(0, 3) for k in keys}} for _ in range(rng.randint(0, 60))]
        assert planner.pareto(cands) == reference_pareto(cands)

    fast, checked = planner.pareto, []

    def compare(cands):
        front = fast(cands)
        assert front == reference_pareto(cands)
        checked.append(len(cands))
        return front

    monkeypatch.setattr(planner, "pareto", compare)
    plan(client, "fld_cantho")
    assert checked and checked[0] > 50


def test_nine_seasons_beam_search(client):
    con = db.connect()
    field = uc.must(con, "fields", "fld_cantho", "FIELD_NOT_FOUND")
    started = time.perf_counter()
    p = uc.make_plan(
        con, field, {"field_id": "fld_cantho", "as_of": AS_OF, "horizon_seasons": 9}, "PLAN"
    )
    elapsed = time.perf_counter() - started
    print(f"n=9 plan: {elapsed:.2f} s, stats={p['stats']}")
    assert elapsed < 10
    assert len(p["windows"]) == 9 and len(p["options"]) >= 2
    base = [s["crop"] for s in p["baseline"]["seasons"]]
    for o in p["options"]:
        crops = [s["crop"] for s in o["seasons"]]
        assert len(crops) == 9 and o["decision_status"] != "NOT_FEASIBLE"
        assert sum(a != b for a, b in zip(crops, base)) <= 1
        assert crops.count("fallow_cover") <= 1
        for a, b in zip(o["seasons"], o["seasons"][1:]):
            assert a["harvest"] < b["sow"]
        assert o["confidence"]["level"] in ("HIGH", "MEDIUM", "LOW")


def test_ac06_sow_shift_is_recomputed_and_explained(client):
    parent = plan(client, "fld_cantho")
    r = client.post(
        f"/v1/plans/{parent['decision_id']}/what-if",
        json={"override": {"sow_shift_days": {"2": -14}}},
    )
    assert r.status_code == 201, r.text
    child = r.json()
    before = {o["sequence_id"]: o for o in [parent["baseline"], *parent["options"]]}
    after = [child["baseline"], *child["options"]]
    common = [o for o in after if o["sequence_id"] in before]
    assert common
    for o in common:
        old = before[o["sequence_id"]]
        assert o["seasons"][1]["sow"] == str(
            dt.date.fromisoformat(old["seasons"][1]["sow"]) - dt.timedelta(days=14)
        )
        m, mo = o["metrics"]["sc_clim"], old["metrics"]["sc_clim"]
        assert (m["irrigation_need"]["value"], m["water_stress_days"]["value"]) != (
            mo["irrigation_need"]["value"],
            mo["water_stress_days"]["value"],
        ) or m["per_season"] != mo["per_season"]
        assert any("Vụ 2 gieo sớm 14 ngày" in reason["text"] for reason in o["reasons"])
    for o in child["options"]:
        assert "Vụ 2 gieo sớm 14 ngày" in o["summary_vi"]
