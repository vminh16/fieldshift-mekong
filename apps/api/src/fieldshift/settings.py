"""Minimal environment configuration; extend with validated settings as needed."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str
    cors_origins: list[str]


def get_settings() -> Settings:
    cors = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return Settings(
        environment=os.getenv("APP_ENV", "development"),
        cors_origins=[value.strip() for value in cors.split(",") if value.strip()],
    )
