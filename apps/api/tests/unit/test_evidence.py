import pytest

from fieldshift.domain.models.scenario import ScenarioKind
from fieldshift.domain.value_objects.evidence import Evidence, EvidenceKind


def test_unknown_is_not_a_number() -> None:
    with pytest.raises(ValueError, match="UNKNOWN"):
        Evidence(value=3.2, kind=EvidenceKind.UNKNOWN)


def test_unknown_without_number_is_allowed() -> None:
    ev = Evidence[float](value=None, kind=EvidenceKind.UNKNOWN)
    assert ev.value is None


def test_scenarios_keep_distinct_semantics() -> None:
    assert ScenarioKind.FORECAST != ScenarioKind.CLIMATE_PROJECTION
    assert ScenarioKind.STRESS_TEST != ScenarioKind.CLIMATOLOGY
