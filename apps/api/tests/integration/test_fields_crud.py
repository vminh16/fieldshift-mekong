from fastapi.testclient import TestClient

from fieldshift.main import app

PARCEL = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[[105.97, 9.60], [105.972, 9.60], [105.972, 9.602], [105.97, 9.60]]],
    },
    "properties": {"place_name": "Sóc Trăng", "area_source": "drawn"},
}


def test_field_keeps_frontend_geometry_and_patches():
    with TestClient(app) as client:
        created = client.post(
            "/v1/fields",
            json={
                "name": "Ruộng sau nhà",
                "lat": 9.601,
                "lon": 105.971,
                "area_ha": 1.2,
                "geometry": PARCEL,
            },
        )
        assert created.status_code == 201, created.text
        field = created.json()
        assert field["geometry"] == PARCEL
        assert field["profile"]["baseline"] is None  # unknown stays unknown (G2 fails)

        patched = client.patch(
            f"/v1/fields/{field['id']}",
            json={"name": "Ruộng gần kênh", "area_ha": 0.9, "lat": 9.605, "lon": 105.975},
        )
        assert patched.status_code == 200
        body = patched.json()
        assert (body["name"], body["lat"], body["lon"]) == ("Ruộng gần kênh", 9.605, 105.975)
        assert body["geometry"] == PARCEL

        outside = client.patch(f"/v1/fields/{field['id']}", json={"lat": 21.0})
        assert outside.status_code == 422


def test_delete_field_removes_its_plans_and_observations():
    with TestClient(app) as client:
        field = client.post(
            "/v1/fields",
            json={
                "name": "Xoá thử",
                "lat": 10.03,
                "lon": 105.78,
                "profile": {"cache_key": "cantho"},
            },
        ).json()
        fid = field["id"]
        obs = client.post(
            f"/v1/fields/{fid}/observations",
            json={
                "variable": "canal_ecw",
                "value": 1.2,
                "unit": "dS/m",
                "observed_at": "2026-11-10",
            },
        )
        assert obs.status_code == 201
        plan = client.post(
            "/v1/plans", json={"field_id": fid, "as_of": "2026-11-14", "horizon_seasons": 1}
        )
        assert plan.status_code == 201, plan.text
        decision_id = plan.json()["decision_id"]
        what_if = client.post(
            f"/v1/plans/{decision_id}/what-if", json={"priorities": ["soil_health"]}
        )
        assert what_if.status_code in (200, 201), what_if.text

        assert client.delete(f"/v1/fields/{fid}").status_code == 204
        assert client.get(f"/v1/fields/{fid}").status_code == 404
        assert client.get(f"/v1/plans/{decision_id}").status_code == 404
        assert all(f["id"] != fid for f in client.get("/v1/fields").json())
        assert client.delete(f"/v1/fields/{fid}").status_code == 404


def test_browser_may_delete_from_the_frontend_origin():
    with TestClient(app) as client:
        preflight = client.options(
            "/v1/fields/fld_x",
            headers={"Origin": "http://localhost:5180", "Access-Control-Request-Method": "DELETE"},
        )
        assert preflight.status_code == 200
        assert "DELETE" in preflight.headers["access-control-allow-methods"]
