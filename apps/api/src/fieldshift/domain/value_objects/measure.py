"""Measure: every displayed number carries unit, origin, label and evidence; unknown stays null + reason."""


def measure(value, unit, origin, label, evidence_ids=(), reason=None) -> dict:
    m = {
        "value": value,
        "unit": unit,
        "origin": origin,
        "label": label,
        "evidence_ids": list(evidence_ids),
    }
    if value is None:
        m["origin"], m["label"], m["reason"] = "unknown", "Chưa biết", reason or "NOT_AVAILABLE"
    return m
