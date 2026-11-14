"""Liveness + catalog/reference endpoints."""

from fastapi import APIRouter, HTTPException

from fieldshift.api.v1.source_catalog import SOURCES
from fieldshift.domain.catalog import CROPS, REGIONS
from fieldshift.domain.engines.rotation_planner import VERSIONS
from fieldshift.infrastructure.persistence.sqlite import now

router = APIRouter(tags=["health"])


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
    used = [s for s in SOURCES if s["is_nasa"] and s["use"] != "NOT_USED"]
    return {
        "sources": SOURCES,
        "generated_at": now(),
        "nasa_used_count": len(used),
        "challenge_sources_used": [s["id"] for s in used if s["in_challenge_list"]],
    }


@router.get("/crops", tags=["catalog"])
def crops():
    return CROPS


@router.get("/regions/{region_id}", tags=["catalog"])
def region(region_id: str):
    if region_id not in REGIONS:
        raise HTTPException(404, {"code": "REGION_NOT_FOUND"})
    return REGIONS[region_id]
