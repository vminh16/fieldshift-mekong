"""G8: fail closed for numeric Measures lacking resolvable evidence references."""

import math


def enforce_evidence(package: dict, evidence: dict) -> None:
    missing = []

    def visit(value, path):
        if isinstance(value, dict):
            number = value.get("value")
            if (
                isinstance(number, (int, float))
                and not isinstance(number, bool)
                and "unit" in value
            ):
                refs = value.get("evidence_ids")
                if (
                    not isinstance(refs, list)
                    or not refs
                    or any(not isinstance(ref, str) or ref not in evidence for ref in refs)
                    or not math.isfinite(number)
                ):
                    value.update(
                        value=None,
                        origin="unknown",
                        label="Chưa biết",
                        reason="EVIDENCE_INCOMPLETE_G8",
                    )
                    missing.append(path)
            for key, item in value.items():
                visit(item, f"{path}.{key}")
        elif isinstance(value, list):
            for i, item in enumerate(value):
                visit(item, f"{path}[{i}]")

    visit(package.get("baseline"), "baseline")
    visit(package.get("options", []), "options")
    package["gates"] = [g for g in package.get("gates", []) if g["gate"] != "G8"] + [
        {
            "gate": "G8",
            "passed": not missing,
            "message": "Every numeric option Measure references existing evidence."
            if not missing
            else "Numbers without complete evidence removed (EVIDENCE_COMPLETE).",
            "missing_evidence_paths": missing,
        }
    ]
