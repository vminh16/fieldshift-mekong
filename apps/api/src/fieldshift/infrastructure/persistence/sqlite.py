"""SQLite persistence. Decisions are immutable JSON snapshots (design v2 §13.3)."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from fieldshift.settings import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS fields (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, region_id TEXT NOT NULL DEFAULT 'mekong',
  lat REAL NOT NULL CHECK (lat BETWEEN -90 AND 90), lon REAL NOT NULL CHECK (lon BETWEEN -180 AND 180),
  geometry JSON, area_ha REAL CHECK (area_ha > 0), profile JSON NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS observations (
  id TEXT PRIMARY KEY, field_id TEXT NOT NULL REFERENCES fields(id), variable TEXT NOT NULL,
  value REAL, value_text TEXT, unit TEXT, observed_at TEXT NOT NULL,
  evidence_kind TEXT NOT NULL CHECK (evidence_kind IN ('OBSERVED_FIELD','REPORTED_BY_FARMER')),
  note TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS field_states (
  id TEXT PRIMARY KEY, field_id TEXT NOT NULL REFERENCES fields(id), as_of TEXT NOT NULL,
  state JSON NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY, field_id TEXT NOT NULL REFERENCES fields(id), parent_id TEXT REFERENCES decisions(id),
  kind TEXT NOT NULL CHECK (kind IN ('PLAN','WHAT_IF','REPLAN')), request JSON NOT NULL,
  field_state_id TEXT NOT NULL REFERENCES field_states(id), versions JSON NOT NULL, package JSON NOT NULL,
  created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_decisions_field ON decisions(field_id, created_at);
CREATE INDEX IF NOT EXISTS ix_obs_field ON observations(field_id, observed_at);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def connect() -> sqlite3.Connection:
    path = get_settings().db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con


JSON_COLS = {"geometry", "profile", "state", "request", "versions", "package"}


def row(r: sqlite3.Row | None) -> dict | None:
    if r is None:
        return None
    return {
        k: (json.loads(r[k]) if k in JSON_COLS and r[k] is not None else r[k]) for k in r.keys()
    }


def insert(con, table: str, data: dict) -> dict:
    vals = {
        k: (
            json.dumps(v, ensure_ascii=False, default=str)
            if k in JSON_COLS and v is not None
            else v
        )
        for k, v in data.items()
    }
    con.execute(
        f"INSERT INTO {table} ({','.join(vals)}) VALUES ({','.join('?' * len(vals))})",
        list(vals.values()),
    )
    con.commit()
    return data


def get(con, table: str, id_: str) -> dict | None:
    return row(con.execute(f"SELECT * FROM {table} WHERE id = ?", (id_,)).fetchone())


def seed_demo_fields(con, region: dict) -> None:
    """Demo fields match cached NASA POWER points so the demo runs offline."""
    for f in region["demo_fields"]:
        if get(con, "fields", f["id"]):
            continue
        t = now()
        insert(
            con,
            "fields",
            {
                "id": f["id"],
                "name": f["name_vi"],
                "region_id": region["id"],
                "lat": f["lat"],
                "lon": f["lon"],
                "geometry": None,
                "area_ha": 1.0,
                "created_at": t,
                "updated_at": t,
                "profile": {
                    "baseline": ["rice", "rice", "rice"],
                    "irrigation": "full",
                    "drainage": "unknown",
                    "coastal_salinity_risk": f["coastal_salinity_risk"],
                    "equipment": [],
                    "history": [],
                    "cache_key": f["cache_key"],
                },
            },
        )
