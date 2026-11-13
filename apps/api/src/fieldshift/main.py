"""ASGI entrypoint; no planning logic belongs here."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fieldshift.api.v1 import fields, health, plans
from fieldshift.application.errors import InvalidInput, NotFound
from fieldshift.domain.catalog import REGIONS
from fieldshift.infrastructure.data_sources.nasa.power import PowerUnavailable
from fieldshift.infrastructure.persistence import sqlite as db
from fieldshift.settings import get_settings


@asynccontextmanager
async def lifespan(_):
    con = db.connect()
    db.seed_demo_fields(con, REGIONS["mekong"])
    con.close()
    yield


settings = get_settings()
app = FastAPI(title="FieldShift-Mekong API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": {"code": code, "message": message}})


@app.exception_handler(NotFound)
def _not_found(_: Request, e: NotFound):
    return _err(404, e.code, e.message)


@app.exception_handler(InvalidInput)
def _invalid(_: Request, e: InvalidInput):
    return _err(422, e.code, e.message)


@app.exception_handler(PowerUnavailable)
def _power_down(_: Request, e: PowerUnavailable):
    return _err(503, "NASA_POWER_UNAVAILABLE", str(e))


app.include_router(health.router, prefix="/v1")
app.include_router(fields.router, prefix="/v1")
app.include_router(plans.router, prefix="/v1")
