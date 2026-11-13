"""Planning endpoints are reserved; do not return mock recommendations as real data."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("")
def create_plan() -> None:
    raise HTTPException(status_code=501, detail="Rotation Planning Engine not implemented")
