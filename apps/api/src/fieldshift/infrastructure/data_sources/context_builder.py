"""Data Integration & Context Builder (design v2 §6.1): adapters -> FieldContext with evidence ledger."""

import datetime as dt

from fieldshift.domain.catalog import CROPS, REGIONS
from fieldshift.infrastructure.crop_models.fao56_water import weather_from_power
from fieldshift.infrastructure.data_sources.local.soilgrids import load_soil
from fieldshift.infrastructure.data_sources.nasa.nasadem import load_elevation
from fieldshift.infrastructure.data_sources.nasa.power import load_power


def build_context(field: dict, as_of: dt.date) -> dict:
    """FieldContext: data restricted to dates < as_of (no look-ahead, AC-04)."""
    region = REGIONS[field["region_id"]]
    ck = field["profile"].get("cache_key")
    payload, power_status = load_power(field["lat"], field["lon"], ck)
    weather = [w for w in weather_from_power(payload) if w["date"] < as_of]
    p = payload["properties"]["parameter"]
    gwet = {
        dt.datetime.strptime(k, "%Y%m%d").date(): v for k, v in p["GWETROOT"].items() if v != -999
    }
    gwet = {d: v for d, v in gwet.items() if d < as_of}
    elev_srtm, srtm_status = load_elevation(field["lat"], field["lon"], ck)
    soil, soil_status = load_soil(field["lat"], field["lon"], region, ck)
    valid = [
        w
        for w in weather
        if None not in (w["tmax"], w["tmin"], w["tdew"], w["rs_mj"], w["u2"], w["rain_mm"])
    ]
    last = max(w["date"] for w in valid) if valid else None

    evidence = {
        "ev_power_daily": {
            "kind": "OBSERVED_REMOTE_ESTIMATE",
            "source": "NASA POWER Daily (MERRA-2/CERES), community AG",
            "version": payload.get("header", {}).get("api", {}).get("version"),
            "spatial_scale": "regional",
            "resolution": "0.5x0.625 deg (~50 km)",
            "time_scope": [str(weather[0]["date"]), str(last)] if weather else None,
            "status": power_status,
            "url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
            "limitations": ["Ô lưới ~50 km, không phải đo tại thửa", "Ô ven biển có thể lẫn biển"],
        },
        "ev_power_gwet": {
            "kind": "MODEL_ESTIMATE",
            "source": "NASA POWER GWETROOT (MERRA-2 root-zone wetness 0-1)",
            "spatial_scale": "regional",
            "status": power_status,
            "limitations": ["Độ ẩm mô hình quy mô vùng, không phải % ẩm tại ruộng"],
        },
        "ev_srtm": {
            "kind": "OBSERVED_REMOTE_ESTIMATE",
            "source": "SRTM 30 m via OpenTopoData",
            "spatial_scale": "field",
            "status": srtm_status,
            "limitations": ["Không thể hiện đê bao/cống; không chứng minh ngập"],
        },
        "ev_soil": {
            "kind": soil["kind"],
            "source": soil["source"],
            "spatial_scale": "regional",
            "status": soil_status,
            "limitations": ["Không thay thế xét nghiệm đất tại thửa"],
        },
        "ev_crop_catalog": {
            "kind": "LITERATURE_RULE",
            "source": "crops.json (" + CROPS["version"] + "): FAO-56, FAO-29, Maas-Hoffman",
            "limitations": ["Tham số tham khảo, chưa hiệu chỉnh giống địa phương"],
        },
        "ev_region_calendar": {
            "kind": "LITERATURE_RULE",
            "source": "regions.json: " + "; ".join(region["sources"]),
            "limitations": region["limitations"],
        },
        "ev_value_heuristic": {
            "kind": "ASSUMPTION",
            "source": "[B] heuristic nhóm: regions.json season_value_weight × crops.json value_index",
            "limitations": region["season_value_weight"]["limitations"]
            + CROPS["value_index"]["limitations"],
        },
        "ev_salinity_season": {
            "kind": "ASSUMPTION",
            "source": "; ".join(region["salinity_season"]["sources"]),
            "limitations": region["salinity_season"]["limitations"],
        },
    }
    if field["profile"].get(
        "coastal_salinity_risk"
    ):  # MERRA-2 0.5° cell partly over sea -> damped Tmax (seen at Soc Trang)
        evidence["ev_power_daily"]["quality_flags"] = ["COASTAL_CELL_MIXED"]
    if power_status == "CACHED_NEARBY_CELL":
        evidence["ev_power_daily"].setdefault("quality_flags", []).append(
            "NEARBY_CELL_OFFLINE_FALLBACK"
        )
    return {
        "region": region,
        "weather": valid,
        "gwet": gwet,
        "last_data_date": last,
        "elevation_m": elev_srtm,
        "grid_elevation_m": payload["geometry"]["coordinates"][2],
        "soil": soil,
        "evidence": evidence,
        "sources_status": {
            "NASA_POWER": power_status,
            "SRTM": srtm_status,
            "SOILGRIDS": soil_status,
        },
    }
