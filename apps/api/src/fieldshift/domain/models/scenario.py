"""Outlook kind is part of the scientific contract; not a UI-only label."""

from enum import StrEnum


class ScenarioKind(StrEnum):
    FORECAST = "FORECAST"
    CLIMATE_PROJECTION = "CLIMATE_PROJECTION"
    CLIMATOLOGY = "CLIMATOLOGY"
    STRESS_TEST = "STRESS_TEST"
