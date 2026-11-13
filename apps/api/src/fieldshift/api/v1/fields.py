"""Field endpoints are reserved; do not fabricate persisted fields."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/fields", tags=["fields"])


@router.post("")
def create_field() -> None:
    raise HTTPException(status_code=501, detail="Field persistence not implemented")
