import datetime as dt

from fieldshift.domain.catalog import REGIONS
from fieldshift.domain.engines.official_guidance import active_region, evidence
from fieldshift.domain.engines.rotation_planner import salinity_window


def test_dated_guidance_does_not_leak_into_hindcast():
    assert evidence(dt.date(2015, 11, 15)) == {}
    assert "ev_siwrr_2026_press" not in evidence(dt.date(2026, 10, 4))


def test_salinity_advance_requires_current_bulletin_and_el_nino():
    as_of = dt.date(2026, 11, 14)
    region = REGIONS["mekong"]
    outlook = {"status": "OK", "enso": {"phase": "EL_NINO_STRONG"}}
    active, adjusted = active_region(region, outlook, as_of, evidence(as_of))
    assert adjusted
    assert salinity_window(active, as_of, 0) == (dt.date(2026, 12, 1), dt.date(2027, 6, 15))
    assert salinity_window(region, as_of, 0)[0] == dt.date(2027, 1, 15)
    assert salinity_window(active, dt.date(2027, 11, 14), 0)[0] == dt.date(2028, 1, 15)
    assert active_region(region, outlook, as_of, {}) == (region, False)
    assert active_region(
        region, {"status": "OK", "enso": {"phase": "NEUTRAL"}}, as_of, evidence(as_of)
    ) == (region, False)
    assert not active_region(region, outlook, dt.date(2025, 11, 14), evidence(as_of))[1]
