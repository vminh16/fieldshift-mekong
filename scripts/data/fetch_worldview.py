"""Download reproducible pitch snapshots; browse images are not quantitative data."""

from __future__ import annotations

import struct
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import httpx
from common import DEFAULT_CACHE, ROOT, get, write_json


def main():
    folder = ROOT / "docs/data/images"
    folder.mkdir(parents=True, exist_ok=True)
    with httpx.Client(
        timeout=120, follow_redirects=True, transport=httpx.HTTPTransport(local_address="0.0.0.0")
    ) as c:
        capabilities = get(
            c, "https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml"
        ).text
        (DEFAULT_CACHE / "worldview").mkdir(parents=True, exist_ok=True)
        (DEFAULT_CACHE / "worldview/capabilities.xml").write_text(capabilities)
        root = ET.fromstring(capabilities)
        ids = [n.text for n in root.findall(".//{http://www.opengis.net/ows/1.1}Identifier")]
        layers = {
            "truecolor": "MODIS_Terra_CorrectedReflectance_TrueColor",
            "ndvi": "MODIS_Terra_L3_NDVI_16Day",
            "precipitation": "IMERG_Precipitation_Rate",
        }
        for name, layer_id in layers.items():
            if layer_id not in ids:
                print(
                    name,
                    "available candidates",
                    [x for x in ids if ("NDVI" in x if name == "ndvi" else "IMERG" in x)],
                    flush=True,
                )
                raise ValueError("Layer ID absent from GIBS capabilities: " + layer_id)
        manifest = []
        for day in ["2016-03-16", "2020-03-15", "2024-03-15", "2024-09-15"]:
            for name, layer in layers.items():
                layer_day = day
                if name == "ndvi":
                    d = date.fromisoformat(day)
                    start = date(d.year, 1, 1)
                    layer_day = (start + timedelta(days=((d - start).days // 16) * 16)).isoformat()
                params = {
                    "REQUEST": "GetSnapshot",
                    "TIME": layer_day,
                    "BBOX": "8.5,104.4,11.2,106.9",
                    "CRS": "EPSG:4326",
                    "LAYERS": layer,
                    "WRAP": "none",
                    "FORMAT": "image/png",
                    "WIDTH": 600,
                    "HEIGHT": 648,
                }
                request = c.build_request(
                    "GET", "https://wvs.earthdata.nasa.gov/api/v1/snapshot", params=params
                )
                path = folder / f"{day}_{name}.png"
                if not path.exists():
                    response = get(c, str(request.url))
                    data = response.content
                    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                        raise ValueError("Snapshot returned non-PNG")
                    if struct.unpack(">II", data[16:24]) != (600, 648):
                        raise ValueError("Unexpected snapshot dimensions")
                    path.write_bytes(data)
                manifest.append(
                    {
                        "date": layer_day,
                        "representative_date": day,
                        "layer": layer,
                        "file": str(path.relative_to(ROOT)),
                        "snapshot_url": str(request.url),
                        "bytes": path.stat().st_size,
                        "bbox_lon_lat": [104.4, 8.5, 106.9, 11.2],
                        "axis_order": "EPSG:4326 WMS latitude,longitude",
                        "note": "Browse only; NDVI is a 16-day composite; precipitation is rate at selected UTC time, not daily accumulation.",
                    }
                )
                write_json(folder / "manifest.json", manifest)
                print(day, name, path.stat().st_size, flush=True)
        if sum(p.stat().st_size for p in folder.glob("*.png")) >= 5_000_000:
            raise ValueError("Snapshot total exceeds 5 MB")


if __name__ == "__main__":
    main()
