"""Plan / what-if / replan use cases (design v2 §8, §11.4, §12). Decisions are immutable snapshots."""

import copy
import datetime as dt

from fieldshift.application.errors import InvalidInput, NotFound
from fieldshift.application.use_cases.outlook_context import add_outlook
from fieldshift.domain.engines.evidence_gate import enforce_evidence
from fieldshift.domain.engines.field_state import estimate_state
from fieldshift.domain.engines.rotation_planner import VERSIONS, rerank_options, run_plan
from fieldshift.domain.engines.trigger_evaluation import evaluate_triggers
from fieldshift.infrastructure.crop_models.fao56_water import simulate_season
from fieldshift.infrastructure.data_sources.context_builder import build_context
from fieldshift.infrastructure.persistence import sqlite as db

DISCLAIMER = (
    "Công cụ hỗ trợ tham khảo, không thay thế quyết định của nông dân và cán bộ khuyến nông."
)
_CTX: dict = {}  # ponytail: unbounded in-process cache, fine for a handful of demo fields


def must(c, table, id_, code):
    x = db.get(c, table, id_)
    if not x:
        raise NotFound(code, f"{id_} not found")
    return x


def observations(c, field_id):
    rows = c.execute(
        "SELECT * FROM observations WHERE field_id = ? ORDER BY observed_at", (field_id,)
    )
    return [db.row(r) for r in rows]


def context_for(field, as_of):
    key = (field["id"], field["updated_at"], as_of, dt.date.today())
    if key not in _CTX:
        _CTX[key] = add_outlook(
            build_context(field, as_of), field, as_of
        )  # may raise PowerUnavailable -> 503
    return _CTX[key]


def public(pkg):
    """Trajectories are served by /twin to keep the decision response small."""
    return {k: v for k, v in pkg.items() if k != "trajectories"}


def make_plan(c, f, req: dict, kind: str, parent_id=None, override=None, history=None):
    as_of = dt.date.fromisoformat(req["as_of"])
    ctx = context_for(f, as_of)
    state = estimate_state(f, ctx, as_of, observations(c, f["id"]))
    try:
        core = run_plan(f, ctx, state, req, override, simulate=simulate_season)
    except ValueError as e:
        raise InvalidInput("PLAN_INPUT_INVALID", str(e)) from e
    st_id = db.new_id("st")
    db.insert(
        c,
        "field_states",
        {
            "id": st_id,
            "field_id": f["id"],
            "as_of": str(as_of),
            "state": state,
            "created_at": db.now(),
        },
    )
    ev = ctx["evidence"]["ev_power_daily"]
    versions = {**VERSIONS, "data": f"power-{ev['version']}@{ctx['last_data_date']}"}
    dec_id = db.new_id("dec")
    pkg = {
        "decision_id": dec_id,
        "parent_id": parent_id,
        "kind": kind,
        "field_id": f["id"],
        "as_of": str(as_of),
        "generated_at": db.now(),
        "versions": versions,
        "field_state_snapshot_id": st_id,
        "field_state": state,
        "request": req,
        "override": override,
        "history": history or [],
        **core,
        "evidence": ctx["evidence"],
        "disclaimer": DISCLAIMER,
    }
    enforce_evidence(pkg, pkg["evidence"])
    if core.get("insufficient"):
        pkg["decision_status"] = "INSUFFICIENT_EVIDENCE"
    db.insert(
        c,
        "decisions",
        {
            "id": dec_id,
            "field_id": f["id"],
            "parent_id": parent_id,
            "kind": kind,
            "request": req,
            "field_state_id": st_id,
            "versions": versions,
            "package": pkg,
            "created_at": db.now(),
        },
    )
    return public(pkg)


def override_effects(override):
    """Compare actual dependencies, including frontend payloads containing empty defaults."""
    effects = {}
    for key, value in (override or {}).items():
        if key == "sow_shift_days":
            value = {season: days for season, days in (value or {}).items() if days}
        if value is not None and value != {} and (key == "irrigation_cap_mm" or value != 0):
            effects[key] = value
    return effects


def what_if(c, decision_id: str, priorities, override):
    parent = must(c, "decisions", decision_id, "DECISION_NOT_FOUND")
    req = dict(parent["request"])
    if priorities is not None:
        req["priorities"] = priorities
    same_override = override is None or override_effects(override) == override_effects(
        parent["package"].get("override")
    )
    if priorities is not None and same_override and "options" in parent["package"]:
        pkg = copy.deepcopy(parent["package"])
        pkg.update(
            decision_id=db.new_id("dec"),
            parent_id=decision_id,
            kind="WHAT_IF",
            generated_at=db.now(),
            request=req,
        )
        pkg["options"] = rerank_options(
            pkg["options"], priorities or ["avoid_crop_failure", "save_water", "soil_health"]
        )
        pkg["computation"] = {
            "mode": "PRIORITIES_ONLY",
            "reused_from": decision_id,
            "season_simulations": 0,
        }
        db.insert(
            c,
            "decisions",
            {
                "id": pkg["decision_id"],
                "field_id": parent["field_id"],
                "parent_id": decision_id,
                "kind": "WHAT_IF",
                "request": req,
                "field_state_id": parent["field_state_id"],
                "versions": parent["versions"],
                "package": pkg,
                "created_at": pkg["generated_at"],
            },
        )
        return public(pkg)
    f = must(c, "fields", parent["field_id"], "FIELD_NOT_FOUND")
    return make_plan(
        c,
        f,
        req,
        "WHAT_IF",
        parent_id=decision_id,
        override=override if override is not None else parent["package"].get("override"),
        history=parent["package"].get("history"),
    )


def replan(c, decision_id: str, as_of: dt.date, completed: list):
    parent = must(c, "decisions", decision_id, "DECISION_NOT_FOUND")
    f = must(c, "fields", parent["field_id"], "FIELD_NOT_FOUND")
    req = dict(parent["request"])
    done = len(completed)
    remaining = req["horizon_seasons"] - done
    if remaining < 1:
        raise InvalidInput("NOTHING_TO_REPLAN", "Tất cả các vụ đã hoàn thành")
    base = req.get("baseline") or f["profile"]["baseline"]
    req.update(
        as_of=str(as_of), horizon_seasons=remaining, baseline=base[done : done + remaining] or None
    )
    for s in completed:
        db.insert(
            c,
            "observations",
            {
                "id": db.new_id("obs"),
                "field_id": f["id"],
                "variable": "season_closed",
                "value": None,
                "value_text": f"{s.crop} {s.sow}→{s.harvest}",
                "unit": None,
                "observed_at": str(s.harvest),
                "evidence_kind": "REPORTED_BY_FARMER",
                "note": s.note,
                "created_at": db.now(),
            },
        )
    history = (parent["package"].get("history") or []) + [
        s.model_dump(mode="json") for s in completed
    ]
    new_obs = [
        o
        for o in observations(c, f["id"])
        if parent["package"]["as_of"] <= o["observed_at"] <= str(as_of)
    ]
    pkg = make_plan(c, f, req, "REPLAN", parent_id=decision_id, history=history)
    pkg["changed_since_parent"] = new_obs
    return pkg


def plan_status(c, decision_id):
    parent = must(c, "decisions", decision_id, "DECISION_NOT_FOUND")
    return evaluate_triggers(parent["package"], observations(c, parent["field_id"]))
