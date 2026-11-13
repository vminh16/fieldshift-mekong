"""Scenario endpoints are reserved; all future kinds require explicit semantics."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post("")
def create_scenario() -> None:
    raise HTTPException(status_code=501, detail="Scenario Engine not implemented")
