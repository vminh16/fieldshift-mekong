"""Season/crop value, fallow stress accounting, inland third-season rest, coastal early sowing."""

import datetime as dt
from dataclasses import replace
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from fieldshift.domain.catalog import REGIONS
from fieldshift.domain.engines import rotation_planner as planner
from fieldshift.infrastructure.persistence import sqlite as db
from fieldshift.main import app

AS_OF = "2026-11-14"


@pytest.fixture(scope="module")
def plans(tmp_path_factory):
    # Demo fields in their original, unobserved state (other tests add observations).
    settings = replace(db.get_settings(), db_path=tmp_path_factory.mktemp("agro") / "agro.db")
    original = db.get_settings
    db.get_settings = lambda: settings
    try:
        with TestClient(app) as c:

            def plan(field_id):
                r = c.post("/v1/plans", json={"field_id": field_id, "as_of": AS_OF})
                assert r.status_code == 201, r.text
                return r.json()

            yield {f: plan(f) for f in ("fld_cantho", "fld_soctrang")}
    finally:
        db.get_settings = original


def by_tag(p, tag):
    return next((o for o in p["options"] if o["strategy_tag"] == tag), None)


def test_cantho_top_pick_keeps_dong_xuan_rice(plans):
    top = plans["fld_cantho"]["options"][0]
    crops = [s["crop"] for s in top["seasons"]]
    assert top["seasons"][0]["window"] == "dong_xuan" and crops[0] == "rice"
    assert crops[1] != "rice" or crops[2] == "fallow_cover"
    assert top["production_value_index"] < plans["fld_cantho"]["baseline"]["production_value_index"]
    assert "Chỉ số giá trị sản xuất" in top["reasons"][0]["text"]


def test_production_value_index_prefers_keeping_dong_xuan_rice():
    region = REGIONS["mekong"]
    windows = planner.window_instances(region, dt.date.fromisoformat(AS_OF), 3)
    sows = [next(o for o in planner.sow_options(w) if o[0] == "standard") for w in windows]

    def pvi(crops):
        return planner.production_value_index(planner.make_sequence(windows, crops, sows), region)

    base = pvi(["rice", "rice", "rice"])
    for crop in ("mungbean", "soybean", "fallow_cover"):
        replace_dx, replace_xh = pvi([crop, "rice", "rice"]), pvi(["rice", crop, "rice"])
        assert replace_dx < replace_xh < base, crop
    assert pvi(["rice", "rice", "fallow_cover"]) > pvi(["fallow_cover", "rice", "rice"])


def test_fallow_season_adds_no_stress(plans):
    stub = SimpleNamespace(
        memo={},
        simulation_keys={"k": "k"},
        weather={"k": []},
        lat=0,
        elev=0,
        region={"paddy": {}},
        soil={},
        cap=None,
        simulate=lambda *a: {"water_stress_days": 9, "heat_stress_days_sensitive": 4},
    )
    sow = dt.date(2027, 7, 1)
    fallow = planner.Evaluator.season(stub, "fallow_cover", sow, "k", 0.5)
    assert (fallow["water_stress_days"], fallow["heat_stress_days_sensitive"]) == (0, 0)
    assert fallow["bare_soil_water_stress_days"] == 9  # raw value kept for the Twin
    rice = planner.Evaluator.season(stub, "rice", sow, "k", 0.5)
    assert rice["water_stress_days"] == 9

    rest = by_tag(plans["fld_cantho"], "third_season_rest")
    fallow_index = [s["crop"] for s in rest["seasons"]].index("fallow_cover")
    for metrics in rest["metrics"].values():
        season = metrics["per_season"][fallow_index]
        assert season["water_stress_days"] == 0 and season["heat_stress_days_sensitive"] == 0


def test_inland_third_season_rest_is_qualitative_practice(plans):
    rest = by_tag(plans["fld_cantho"], "third_season_rest")
    assert rest["strategy_name_vi"] == "Nghỉ vụ ba / xả lũ"
    assert [s["crop"] for s in rest["seasons"]] == ["rice", "rice", "fallow_cover"]
    assert rest["seasons"][2]["window"] == "thu_dong"
    lead = rest["reasons"][0]
    assert lead["claim_type"] == "POTENTIAL_QUALITATIVE" and "rầy nâu" in lead["text"]
    assert by_tag(plans["fld_soctrang"], "third_season_rest") is None


def test_soctrang_shortlists_early_sowing_salinity_avoidance(plans):
    p = plans["fld_soctrang"]
    option = by_tag(p, "salinity_avoidance")
    assert option is not None and option["strategy_name_vi"] == "Né mặn: xuống giống sớm"
    assert [s["crop"] for s in option["seasons"]] == [s["crop"] for s in p["baseline"]["seasons"]]
    assert option["seasons"][0]["window"] == "dong_xuan"
    assert option["seasons"][0]["sow_timing"] == "early"
    avoided = option["salinity_overlap_avoided_days"]
    assert avoided["typical"] > 0 and avoided["early_onset"] >= 0
    assert f"bớt {avoided['typical']} ngày" in option["reasons"][0]["text"]
    # Not a salinity-safety claim: the ECw check is still required.
    assert "ECw" in option["reasons"][0]["text"]
    assert any(r["rule_id"] == "R_SALINITY_UNKNOWN" for r in option["rules"])
    assert by_tag(plans["fld_cantho"], "salinity_avoidance") is None
