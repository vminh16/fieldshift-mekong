import copy

from fieldshift.domain.engines.evidence_gate import enforce_evidence
from fieldshift.domain.value_objects.measure import measure


def test_g8_nested_numeric_measures_drop_unresolvable_numbers():
    valid = measure(12, "mm", "inferred_by_model", "Dự kiến", ["existing"])
    missing = measure(22, "mm", "inferred_by_model", "Dự kiến", ["missing"])
    empty = measure(33, "mm", "inferred_by_model", "Dự kiến")
    unknown = measure(None, "mm", "unknown", "Chưa biết", reason="NOT_CALIBRATED")
    package = {
        "options": [
            {
                "metrics": {"ok": valid, "nested": [missing, empty, unknown]},
                "delta_vs_baseline": {"scenario": {"metric": {"value": 44, "unit": "mm"}}},
            }
        ]
    }
    enforce_evidence(package, {"existing": {"source": "real source"}})
    assert valid["value"] == 12
    assert all(
        m["value"] is None and m["reason"] == "EVIDENCE_INCOMPLETE_G8" for m in [missing, empty]
    )
    assert unknown["reason"] == "NOT_CALIBRATED"
    assert package["options"][0]["delta_vs_baseline"]["scenario"]["metric"]["value"] is None
    assert not package["gates"][0]["passed"]
    assert len(package["gates"][0]["missing_evidence_paths"]) == 3


def test_g8_valid_and_unknown_pass():
    package = {
        "options": [
            {
                "metrics": [
                    measure(1, "mm", "inferred_by_model", "Dự kiến", ["ev"]),
                    measure(None, "mm", "unknown", "Chưa biết"),
                ]
            }
        ]
    }
    before = copy.deepcopy(package)
    enforce_evidence(package, {"ev": {}})
    assert package["options"] == before["options"]
    assert package["gates"][0]["passed"]
