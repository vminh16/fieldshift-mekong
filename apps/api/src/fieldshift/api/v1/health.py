"""Liveness + catalog/reference endpoints."""

from fastapi import APIRouter, HTTPException

from fieldshift.domain.catalog import CROPS, REGIONS
from fieldshift.domain.engines.rotation_planner import VERSIONS
from fieldshift.infrastructure.persistence.sqlite import now

router = APIRouter(tags=["health"])

SOURCES = [
    {
        "id": "NASA_POWER",
        "status": "LIVE_OR_CACHED",
        "auth": False,
        "resolution": "0.5x0.625 deg",
        "role": "climate_history, ET0, root-zone wetness",
    },
    {
        "id": "SRTM",
        "status": "LIVE_OR_CACHED",
        "auth": False,
        "resolution": "30 m",
        "role": "terrain_features",
    },
    {
        "id": "SOILGRIDS",
        "status": "OFTEN_UNAVAILABLE",
        "auth": False,
        "resolution": "250 m",
        "role": "soil prior (fallback: regional prior)",
    },
    {
        "id": "NASA_POWER_PROJECTION",
        "status": "UNAVAILABLE",
        "auth": False,
        "note": "Returns -999 for Asian points (tested 2026-11-13)",
    },
    {"id": "SEASONAL_FORECAST", "status": "UNAVAILABLE", "note": "No verified provider (gate G6)"},
    {
        "id": "SALINITY_OBSERVATIONS",
        "status": "USER_INPUT_ONLY",
        "note": "ECw via /v1/fields/{id}/observations",
    },
]


@router.get("/health")
def get_health() -> dict:
    return {
        "status": "ok",
        "service": "fieldshift-api",
        "mode": "mvp",
        "versions": VERSIONS,
        "time": now(),
    }


@router.get("/sources", tags=["catalog"])
def sources():
    return {"sources": SOURCES}


@router.get("/crops", tags=["catalog"])
def crops():
    return CROPS


@router.get("/regions/{region_id}", tags=["catalog"])
def region(region_id: str):
    if region_id not in REGIONS:
        raise HTTPException(404, {"code": "REGION_NOT_FOUND"})
    return REGIONS[region_id]
