"""Public liveness endpoint; not a model/readiness guarantee."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok", "service": "fieldshift-api", "mode": "scaffold"}
