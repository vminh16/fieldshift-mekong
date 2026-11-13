"""ASGI entrypoint; no planning logic belongs here."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fieldshift.api.v1 import fields, health, plans, scenarios
from fieldshift.settings import get_settings

settings = get_settings()
app = FastAPI(title="FieldShift-Mekong API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(health.router, prefix="/v1")
app.include_router(fields.router, prefix="/v1")
app.include_router(plans.router, prefix="/v1")
app.include_router(scenarios.router, prefix="/v1")
