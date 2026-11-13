"""Environment configuration."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    environment: str
    cors_origins: list[str]
    data_dir: Path  # writable: NASA cache for new fields + SQLite
    db_path: Path


@lru_cache
def get_settings() -> Settings:
    cors = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    data_dir = Path(os.getenv("FIELDSHIFT_DATA_DIR", ".fieldshift")).resolve()
    return Settings(
        environment=os.getenv("APP_ENV", "development"),
        cors_origins=[value.strip() for value in cors.split(",") if value.strip()],
        data_dir=data_dir,
        db_path=Path(os.getenv("FIELDSHIFT_DB", data_dir / "fieldshift.db")),
    )
