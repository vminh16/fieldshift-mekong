"""Request contracts (validated at the trust boundary). Responses follow docs/02 §4.4–4.5."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from fieldshift.domain.catalog import CROP_BY_ID

CropId = Literal[tuple(CROP_BY_ID)]  # type: ignore[valid-type]
Priority = Literal[
    "save_water", "avoid_crop_failure", "soil_health", "supplemental_income", "minimal_change"
]
Irrigation = Literal["full", "canal_limited", "rainfed"]
Drainage = Literal["good", "poor", "unknown"]


class FieldProfile(BaseModel):
    # None = the farmer has not told us. Never default these to a value: the state would then
    # label an assumption as "reported_by_farmer" and gate G2 would always pass.
    baseline: list[CropId] | None = Field(default=None, min_length=1, max_length=6)
    irrigation: Irrigation | None = None
    drainage: Drainage | None = None
    coastal_salinity_risk: bool = False
    equipment: list[str] = []
    history: list[dict] = []
    cache_key: str | None = None


class FieldIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    lat: float = Field(ge=8.0, le=11.5, description="MVP: Mekong Delta only")
    lon: float = Field(ge=104.0, le=107.5)
    region_id: Literal["mekong"] = "mekong"
    area_ha: float | None = Field(default=None, gt=0, le=10000)
    geometry: dict | None = None
    profile: FieldProfile = FieldProfile()


class FieldPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    # Redrawing a parcel moves its centroid; NASA context is fetched for these coordinates.
    lat: float | None = Field(default=None, ge=8.0, le=11.5)
    lon: float | None = Field(default=None, ge=104.0, le=107.5)
    area_ha: float | None = Field(default=None, gt=0, le=10000)
    geometry: dict | None = None
    profile: FieldProfile | None = None


class ObservationIn(BaseModel):
    variable: Literal["canal_ecw", "soil_ph", "drainage", "rain_mm", "season_closed"]
    value: float | None = None
    value_text: str | None = Field(default=None, max_length=500)
    unit: str | None = Field(default=None, max_length=20)
    observed_at: date
    evidence_kind: Literal["OBSERVED_FIELD", "REPORTED_BY_FARMER"] = "REPORTED_BY_FARMER"
    note: str | None = Field(default=None, max_length=1000)


class Constraints(BaseModel):
    no_new_machinery: bool = True
    budget_level: Literal["low", "medium", "high"] | None = None
    irrigation: Irrigation | None = None
    irrigation_cap_mm: float | None = Field(default=None, ge=0, le=3000)
    max_changed_seasons: int = Field(default=1, ge=0, le=6)
    max_fallow_seasons: int = Field(default=1, ge=0, le=6)


class PlanRequest(BaseModel):
    field_id: str
    as_of: date | None = None
    horizon_seasons: int = Field(default=3, ge=1, le=3)
    baseline: list[CropId] | None = None
    priorities: list[Priority] = ["avoid_crop_failure", "save_water", "soil_health"]
    constraints: Constraints = Constraints()
    outlook_modes: list[Literal["CLIMATOLOGY", "STRESS_TEST", "FORECAST", "CLIMATE_PROJECTION"]] = [
        "CLIMATOLOGY",
        "STRESS_TEST",
    ]


class ScenarioOverride(BaseModel):
    rain_delta_pct: float | None = Field(default=None, ge=-90, le=200)
    temp_delta_c: float | None = Field(default=None, ge=-5, le=6)
    salinity_onset_shift_weeks: int | None = Field(default=None, ge=-12, le=12)
    sow_shift_days: dict[str, int] = Field(
        default_factory=dict, description='{"2": -10} = vụ 2 gieo sớm 10 ngày'
    )
    irrigation_cap_mm: float | None = Field(default=None, ge=0, le=3000)


class EvaluateChainIn(BaseModel):
    """A rotation chosen by the user, one crop per season of the parent decision's horizon."""

    crops: list[CropId] = Field(min_length=1, max_length=3)
    # Keep an engine option's own timing when re-running it; default is the standard sow date.
    sow_timing: list[Literal["early", "standard"]] | None = None
    # User assumptions (what-if). None keeps the parent's override.
    override: ScenarioOverride | None = None


class WhatIfIn(BaseModel):
    override: ScenarioOverride | None = None
    priorities: list[Priority] | None = None


class CompletedSeason(BaseModel):
    crop: CropId
    sow: date
    harvest: date
    note: str | None = Field(default=None, max_length=500)


class ReplanIn(BaseModel):
    as_of: date
    completed: list[CompletedSeason] = Field(min_length=1)
