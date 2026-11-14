"""Read GAEZ v4 point pixels from FAO's public ArcGIS ImageServer, locking each raster."""

from __future__ import annotations

import concurrent.futures
import json
import math

import httpx
from common import DEFAULT_CACHE, SITES, get, write_json
from observations import publish

BASE = "https://gaez-services.fao.org/server/rest/services/"
CACHE = DEFAULT_CACHE / "gaez"


def main():
    with httpx.Client(timeout=60, transport=httpx.HTTPTransport(local_address="0.0.0.0")) as client:
        params = {
            "f": "json",
            "where": "year='1981-2010' AND model='CRUTS32' AND crop IN ('Wetland rice','Maize','Soybean','Groundnut') AND sub_theme_name='Suitability Index'",
            "outFields": "*",
            "returnGeometry": "false",
            "resultRecordCount": 1000,
        }
        catalog = get(client, BASE + "res05/ImageServer/query", params=params).json()
        if catalog.get("exceededTransferLimit") or "error" in catalog:
            raise ValueError("Incomplete GAEZ catalog")
        crops = [f["attributes"] for f in catalog["features"]]
        # All land suitability, high/low management, irrigation and rainfed. No averaging of distinct layers.
        crops = [
            r
            for r in crops
            if r["variable"].startswith("Suitability index ")
            and r["input_level"] in ("High", "Low")
            and (
                ("all land in grid cell" in r["variable"] and "Rainfed" in r["water_supply"])
                or "Irrigation" in r["water_supply"]
            )
        ]
        lr = get(
            client,
            BASE + "LR/ImageServer/query",
            params={
                "f": "json",
                "where": "sub_theme_name='Soil Resources'",
                "outFields": "*",
                "returnGeometry": "false",
                "resultRecordCount": 1000,
            },
        ).json()
        soils = [
            f["attributes"]
            for f in lr["features"]
            if any(
                w in f["attributes"]["variable"]
                for w in ["salinity", "Nutrient", "Oxygen", "Rooting", "limiting soil"]
            )
        ]
        selected = [("res05", r) for r in crops] + [("LR", r) for r in soils]
        write_json(CACHE / "selected_layers.json", selected)

    def fetch(job):
        service, layer, site = job
        path = (
            CACHE
            / "points"
            / service
            / (str(layer.get("objectid", layer.get("OBJECTID"))) + "_" + site + ".json")
        )
        point = SITES[site]
        if path.exists():
            data = json.loads(path.read_text())
        else:
            params = {
                "f": "json",
                "geometry": f"{point['longitude']},{point['latitude']}",
                "geometryType": "esriGeometryPoint",
                "sr": 4326,
                "returnGeometry": "false",
                "returnCatalogItems": "false",
                "mosaicRule": json.dumps(
                    {
                        "mosaicMethod": "esriMosaicLockRaster",
                        "lockRasterIds": [layer.get("objectid", layer.get("OBJECTID"))],
                    }
                ),
                "renderingRule": json.dumps({"rasterFunction": "None"}),
            }
            with httpx.Client(
                timeout=90, transport=httpx.HTTPTransport(local_address="0.0.0.0")
            ) as c:
                response = get(c, BASE + service + "/ImageServer/identify", params=params)
                data = response.json()
            if "error" in data:
                raise ValueError(str(data["error"]))
            write_json(path, data)
        raw = data["value"]
        value = None if raw in ("NoData", "No Data", "") else float(raw)
        variable = layer["variable"]
        return site, {
            "date": "1981-01-01" if service == "res05" else "2010-01-01",
            "layer_id": layer.get("objectid", layer.get("OBJECTID")),
            "layer_name": layer.get("name", layer.get("Name")),
            "variable": variable,
            "crop": layer.get("crop"),
            "water_supply": layer.get("water_supply"),
            "input_level": layer.get("input_level"),
            "value": value,
            "unit": "index_0_10000" if service == "res05" else layer["units"],
            "scale_applied": 1,
            "download_url": layer["download_url"].strip(),
            "description": layer["file_description"],
        }

    tables = {s: [] for s in SITES}
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        for site, row in pool.map(
            fetch, [(service, r, s) for service, r in selected for s in SITES]
        ):
            tables[site].append(row)
    for site, series in tables.items():
        p = SITES[site]
        resolution = 1 / 12
        publish(
            "gaez",
            site,
            product="FAO GAEZ v4 suitability and soil resources",
            version="4",
            variables={
                "suitability": {"unit": "index_0_10000", "scale_applied": 1},
                "soil_constraint": {
                    "unit": "per-layer class or rating (see series)",
                    "scale_applied": 1,
                },
            },
            resolution="5 arc-minute suitability; soil layers native 30 arc-second",
            cell={
                "longitude": -180
                + (math.floor((p["longitude"] + 180) / resolution) + 0.5) * resolution,
                "latitude": -90
                + (math.floor((p["latitude"] + 90) / resolution) + 0.5) * resolution,
            },
            series=series,
            qa={
                "note": "Rainfed indices cover all land; irrigation variants cover current cropland. Keep this distinction when comparing. Static regional prior. Crop baseline 1981–2010; soil 2010 baseline. Dates are baseline labels, not observations. Raw indices retained; divide by 100 only for display percent. Soil values retain source classes/ratings; no thresholds inferred.",
                "mungbean": "Not present in 51-crop catalog; cowpea/gram not substituted.",
                "missing_pixels": sum(r["value"] is None for r in series),
            },
            license="FAO GAEZ v4 terms; cite FAO/IIASA 2021; https://www.fao.org/gaez/gaezv4/en",
            layer_cell_centers={
                "soil": "[UNVERIFIED] Soil pixel center not independently derived; LR ImageServer advertises a 30 arc-second service grid."
            },
        )
        print(site, len(series), "layers", flush=True)


if __name__ == "__main__":
    main()
