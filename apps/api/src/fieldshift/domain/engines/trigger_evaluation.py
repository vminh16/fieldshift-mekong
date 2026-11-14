"""Evaluate machine-readable adaptation triggers without mutating a decision."""


def evaluate_triggers(package: dict, observations: list[dict]) -> dict:
    fired = []
    options = [package.get("baseline", {}), *package.get("options", [])]
    for option in options:
        for trigger in option.get("triggers", []):
            for obs in observations:
                if obs["observed_at"] < package["as_of"] or obs["variable"] != trigger.get(
                    "variable"
                ):
                    continue
                # Same-day readings count only when entered after the plan was generated
                # (readings existing at planning time were already plan inputs).
                if obs.get("created_at", "") < package["generated_at"]:
                    continue
                value = obs.get("value_text") if trigger["op"] == "eq" else obs.get("value")
                if value is None or obs.get("unit") != trigger.get("unit"):
                    continue
                threshold = trigger["threshold"]
                matches = (trigger["op"] == "gt" and value > threshold) or (
                    trigger["op"] == "eq" and value == threshold
                )
                if matches:
                    fired.append(
                        {
                            "sequence_id": option["sequence_id"],
                            "observation_id": obs["id"],
                            "observed_at": obs["observed_at"],
                            "value": value,
                            **trigger,
                        }
                    )
    return {
        "decision_id": package["decision_id"],
        "status": "REPLAN_REQUIRED" if fired else "OK",
        "fired": fired,
    }
