"""P0 data-integrity checks: assumed defaults, dead machinery rule (AC-07), CMIP6 hindcast leak."""

from fastapi.testclient import TestClient

from fieldshift.domain.catalog import CROP_BY_ID
from fieldshift.main import app

AS_OF = "2026-11-14"


def new_field(client, profile=None):
    r = client.post(
        "/v1/fields",
        json={
            "name": "Integrity",
            "lat": 10.03,
            "lon": 105.78,
            "profile": {"cache_key": "cantho", **(profile or {})},
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def plan(client, field, as_of=AS_OF, **kw):
    r = client.post(
        "/v1/plans", json={"field_id": field["id"], "as_of": as_of, "horizon_seasons": 1, **kw}
    )
    assert r.status_code == 201, r.text
    return r.json()


def g2(p):
    return next(g for g in p["gates"] if g["gate"] == "G2")


def test_missing_profile_is_assumed_not_farmer_reported():
    with TestClient(app) as client:
        bare = new_field(client)
        assert bare["profile"]["baseline"] is None and bare["profile"]["irrigation"] is None
        explicit = new_field(client, {"baseline": ["rice", "rice", "rice"], "irrigation": "full"})
        pb, pe = plan(client, bare), plan(client, explicit)

        assert g2(pb)["passed"] is False and "GIẢ ĐỊNH" in g2(pb)["message"]
        assert g2(pe)["passed"] is True

        sb = client.get(f"/v1/fields/{bare['id']}/context", params={"as_of": AS_OF}).json()["state"]
        se = client.get(f"/v1/fields/{explicit['id']}/context", params={"as_of": AS_OF}).json()[
            "state"
        ]
        assert sb["irrigation"]["origin"] == "assumed_default"
        assert sb["irrigation"]["label"] == "Giả định mặc định"
        assert se["irrigation"]["origin"] == "reported_by_farmer"
        assert sb["drainage"]["origin"] == "unknown"

        # Computation is identical to an explicit irrigation:"full" / rice baseline field.
        assert pb["irrigation_cap_mm_per_season"] is None
        assert pb["baseline"]["metrics"] == pe["baseline"]["metrics"]
        assert [o["metrics"] for o in pb["options"]] == [o["metrics"] for o in pe["options"]]


def test_ac07_no_new_machinery_excludes_machinery_crops(monkeypatch):
    # The shipped catalog has machinery_required == [] for every crop (see docs/RULES.md [C]):
    # filling it changes the pinned fixture shortlist stats. Prove the rule end-to-end on a
    # catalog copy where maize needs a machine.
    monkeypatch.setitem(CROP_BY_ID["maize"], "machinery_required", ["máy tuốt ngô"])
    mech = {c for c, v in CROP_BY_ID.items() if v["machinery_required"]}
    assert mech == {"maize"}
    with TestClient(app) as client:
        f = new_field(client)
        strict = plan(client, f, constraints={"no_new_machinery": True})
        for o in strict["options"]:
            assert not {s["crop"] for s in o["seasons"]} & mech, o["sequence_id"]
            assert o["decision_status"] != "RECOMMEND_FOR_CONSIDERATION" or not any(
                r["rule_id"] == "R_MACHINERY" for r in o["rules"]
            )
        hit = [e for e in strict["excluded"] if e["rule_id"] == "R_MACHINERY"]
        assert hit and all("maize" in e["crops"] and e["severity"] == "HARD" for e in hit)

        loose = plan(client, f, constraints={"no_new_machinery": False})
        assert not any(e["rule_id"] == "R_MACHINERY" for e in loose["excluded"])
        # Machinery crops are evaluated again (and may be shortlisted) once machinery is allowed.
        assert loose["stats"]["evaluated_feasible"] > strict["stats"]["evaluated_feasible"]


def test_hindcast_has_no_cmip6_projection():
    with TestClient(app) as client:
        f = new_field(client)
        modes = ["CLIMATOLOGY", "STRESS_TEST", "CLIMATE_PROJECTION"]
        old = plan(client, f, as_of="2015-11-15", outlook_modes=modes)
        assert all(s["kind"] != "CLIMATE_PROJECTION" for s in old["scenarios"])
        assert any("PROJECTION_UNAVAILABLE_AT_AS_OF" in n for n in old["notes"])
        ctx = client.get(f"/v1/fields/{f['id']}/context", params={"as_of": "2015-11-15"}).json()
        assert ctx["sources_status"]["NEX_GDDP_CMIP6"] == "PROJECTION_UNAVAILABLE_AT_AS_OF"

        now = plan(client, f, outlook_modes=modes)
        assert any(s["kind"] == "CLIMATE_PROJECTION" for s in now["scenarios"])
        assert not any("PROJECTION_UNAVAILABLE_AT_AS_OF" in n for n in now["notes"])
