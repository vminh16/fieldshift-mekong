"""Field profile, observations and context endpoints."""

import datetime as dt
import json

from fastapi import APIRouter, HTTPException

from fieldshift.api.schemas.requests import FieldIn, FieldPatch, ObservationIn
from fieldshift.application.use_cases.plan_rotation import context_for, must, observations
from fieldshift.domain.engines.field_state import climate_summary, estimate_state
from fieldshift.infrastructure.persistence import sqlite as db

router = APIRouter(prefix="/fields", tags=["fields"])


@router.get("")
def list_fields():
    return [db.row(r) for r in db.connect().execute("SELECT * FROM fields ORDER BY created_at")]


@router.post("", status_code=201)
def create_field(body: FieldIn):
    t = db.now()
    data = {
        "id": db.new_id("fld"),
        **body.model_dump(mode="json"),
        "created_at": t,
        "updated_at": t,
    }
    return db.insert(db.connect(), "fields", data)


@router.get("/{field_id}")
def get_field(field_id: str):
    c = db.connect()
    f = must(c, "fields", field_id, "FIELD_NOT_FOUND")
    f["observations"] = observations(c, field_id)
    return f


@router.patch("/{field_id}")
def patch_field(field_id: str, body: FieldPatch):
    c = db.connect()
    f = must(c, "fields", field_id, "FIELD_NOT_FOUND")
    upd = body.model_dump(mode="json", exclude_unset=True)
    if "profile" in upd:
        upd["profile"] = {
            **f["profile"],
            **upd["profile"],
            "cache_key": f["profile"].get("cache_key"),
        }
    upd["updated_at"] = db.now()
    sets = ", ".join(f"{k} = ?" for k in upd)  # keys come from the pydantic model, not the client
    vals = [
        json.dumps(v, ensure_ascii=False) if k in db.JSON_COLS and v is not None else v
        for k, v in upd.items()
    ]
    c.execute(f"UPDATE fields SET {sets} WHERE id = ?", [*vals, field_id])
    c.commit()
    return get_field(field_id)


@router.post("/{field_id}/observations", status_code=201)
def add_observation(field_id: str, body: ObservationIn):
    c = db.connect()
    must(c, "fields", field_id, "FIELD_NOT_FOUND")
    if body.variable == "canal_ecw" and (body.value is None or not 0 <= body.value <= 60):
        raise HTTPException(
            422, {"code": "ECW_OUT_OF_RANGE", "message": "ECw phải là số 0–60 dS/m"}
        )
    data = {
        "id": db.new_id("obs"),
        "field_id": field_id,
        **body.model_dump(mode="json"),
        "created_at": db.now(),
    }
    return db.insert(c, "observations", data)


@router.get("/{field_id}/context")
def field_context(field_id: str, as_of: dt.date | None = None):
    c = db.connect()
    f = must(c, "fields", field_id, "FIELD_NOT_FOUND")
    as_of = as_of or dt.date.today()
    ctx = context_for(f, as_of)
    state = estimate_state(f, ctx, as_of, observations(c, field_id))
    return {
        "field_id": field_id,
        "as_of": str(as_of),
        "state": state,
        "climate": climate_summary(ctx["weather"]),
        "sources_status": ctx["sources_status"],
        "evidence": ctx["evidence"],
    }


@router.get("/{field_id}/plans", tags=["plans"])
def list_plans(field_id: str):
    rows = db.connect().execute(
        "SELECT id, kind, parent_id, created_at FROM decisions WHERE field_id = ? ORDER BY created_at",
        (field_id,),
    )
    return [
        {
            "decision_id": r["id"],
            "kind": r["kind"],
            "parent_id": r["parent_id"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]
