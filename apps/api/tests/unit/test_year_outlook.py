import datetime as dt

import pytest

from fieldshift.domain.engines.future_outlook import (
    enso_analogs,
    enso_phase,
    season_rain_mm,
    year_outlook,
)
from fieldshift.infrastructure.data_sources.enso import latest_oni


@pytest.mark.parametrize(
    "as_of, expected",
    [
        ("2026-11-14", (2026, 9, 2.46)),  # ASO window ends Oct < Nov
        ("2015-11-15", (2015, 9, 2.02)),
        ("2026-12-01", (2026, 9, 2.46)),  # SON (centre Oct) would be usable but is missing
        ("2026-10-31", (2026, 8, 2.12)),  # ASO ends in October = as_of month: not yet usable
    ],
)
def test_latest_oni_never_looks_ahead(as_of, expected):
    assert latest_oni(dt.date.fromisoformat(as_of)) == expected


def test_latest_oni_month_rule_across_year_boundary():
    oni = {(2019, 12): 0.5, (2020, 1): 1.0}
    assert latest_oni(dt.date(2020, 2, 15), oni) == (2019, 12, 0.5)  # DJF ends Feb
    assert latest_oni(dt.date(2020, 3, 1), oni) == (2020, 1, 1.0)
    assert latest_oni(dt.date(2019, 12, 31), oni) is None


@pytest.mark.parametrize(
    "value, phase",
    [
        (2.46, "EL_NINO_STRONG"),
        (1.5, "EL_NINO_STRONG"),
        (0.5, "EL_NINO"),
        (0.49, "NEUTRAL"),
        (-0.49, "NEUTRAL"),
        (-0.5, "LA_NINA"),
        (-1.5, "LA_NINA_STRONG"),
    ],
)
def test_enso_phase_thresholds(value, phase):
    assert enso_phase(value) == phase


def test_analogs_same_family_nearest_first():
    oni = {(y, 9): v for y, v in {2001: 0.6, 2002: 1.9, 2003: -1.0, 2004: 0.2, 2005: 1.2}.items()}
    latest = (2026, 9, 2.0)
    # strong and weak El Niño share the family; neutral/La Niña years are excluded
    assert enso_analogs(oni, latest, dt.date(2026, 11, 14), range(2001, 2006)) == [
        2002,
        2005,
        2001,
    ]
    assert enso_analogs(oni, (2026, 9, 0.0), dt.date(2026, 11, 14), range(2001, 2006)) == [2004]


def test_season_rain_only_after_season_ended():
    monthly = {(y, m): 10.0 for y in (2025, 2026) for m in range(1, 13)}
    assert season_rain_mm(monthly, 2025, dt.date(2026, 4, 20)) is None  # April not over
    assert season_rain_mm(monthly, 2025, dt.date(2026, 5, 1)) == 50.0
    del monthly[(2026, 2)]
    assert season_rain_mm(monthly, 2025, dt.date(2026, 5, 1)) is None  # incomplete season


def test_too_few_analogs_is_unavailable():
    ctx = {
        "enso": {
            "oni": {(2026, 9): 2.46, (2015, 9): 2.0},
            "latest": (2026, 9, 2.46),
            "source": "x",
            "imerg_source": "y",
        },
        "weather": [],
    }
    out = year_outlook(ctx, dt.date(2026, 11, 14), [2015, 2016])
    assert out["status"] == "UNAVAILABLE" and out["reason"] == "TOO_FEW_ANALOG_YEARS"
    assert out["scenario_id"] is None
    missing = year_outlook({"weather": []}, dt.date(2026, 11, 14), [2015])
    assert missing["reason"] == "ONI_NOT_AVAILABLE_AT_AS_OF" and missing["enso"] is None
