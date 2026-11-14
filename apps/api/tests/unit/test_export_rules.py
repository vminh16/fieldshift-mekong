import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[4] / "scripts" / "export_rules.py"


def test_rules_doc_lists_every_planner_rule_and_is_deterministic():
    spec = importlib.util.spec_from_file_location("export_rules", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    text, digest = mod.build()
    ids = {rid for rid, _ in mod.planner_rules()}
    assert {"R_WINDOW", "R_MACHINERY", "R_HEAT"} <= ids
    assert all(f"| {rid} |" in text for rid in ids)
    assert "chưa phân loại" not in text, "new rule without a note in export_rules.RULE_NOTES"
    assert digest in text and mod.build()[1] == digest
