"""Decision endpoints: plan, what-if, replan, twin slice, 1-page export."""

import datetime as dt
import html

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from fieldshift.api.schemas.requests import PlanRequest, ReplanIn, WhatIfIn
from fieldshift.application.use_cases import plan_rotation as uc
from fieldshift.application.use_cases.plan_rotation import must
from fieldshift.infrastructure.persistence import sqlite as db

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("", status_code=201)
def create_plan(body: PlanRequest):
    c = db.connect()
    f = must(c, "fields", body.field_id, "FIELD_NOT_FOUND")
    req = body.model_dump(mode="json")
    req["as_of"] = req["as_of"] or str(dt.date.today())
    return uc.make_plan(c, f, req, "PLAN")


@router.get("/{decision_id}")
def get_plan(decision_id: str):
    return uc.public(must(db.connect(), "decisions", decision_id, "DECISION_NOT_FOUND")["package"])


@router.get("/{decision_id}/status")
def plan_status(decision_id: str):
    return uc.plan_status(db.connect(), decision_id)


@router.post("/{decision_id}/what-if", status_code=201)
def what_if(decision_id: str, body: WhatIfIn):
    override = body.override.model_dump(mode="json") if body.override else None
    return uc.what_if(db.connect(), decision_id, body.priorities, override)


@router.post("/{decision_id}/replan", status_code=201)
def replan(decision_id: str, body: ReplanIn):
    return uc.replan(db.connect(), decision_id, body.as_of, body.completed)


@router.get("/{decision_id}/twin")
def twin(decision_id: str, sequence_id: str, scenario_id: str = "sc_clim"):
    pkg = must(db.connect(), "decisions", decision_id, "DECISION_NOT_FOUND")["package"]
    t = pkg.get("trajectories", {}).get(sequence_id, {}).get(scenario_id)
    if t is None:
        raise uc.NotFound(
            "TRAJECTORY_NOT_FOUND", "sequence_id/scenario_id không có trong decision này"
        )
    return {"decision_id": decision_id, "sequence_id": sequence_id, "scenario_id": scenario_id, **t}


@router.get("/{decision_id}/export", response_class=HTMLResponse)
def export(decision_id: str):
    p = must(db.connect(), "decisions", decision_id, "DECISION_NOT_FOUND")["package"]
    e = html.escape
    rows = ""
    for o in [p["baseline"], *p["options"]]:
        m = o["metrics"]["sc_clim"]
        rows += (
            f"<tr><td>{'Hiện tại' if o['is_baseline'] else e(o['strategy_name_vi'] or '')}</td>"
            f"<td>{' → '.join(e(s['crop_name_vi']) + ' (' + s['sow'] + ')' for s in o['seasons'])}</td>"
            f"<td>{e(o['decision_status'])}</td><td>{m['irrigation_need']['value']} mm</td>"
            f"<td>{'<br>'.join(e(r['text']) for r in o['reasons']) or '—'}</td>"
            f"<td>{'<br>'.join(e(x) for x in o['checklist']) or '—'}</td></tr>"
        )
    gates = "".join(
        f"<li>{e(g['gate'])}: {e(g['message'])}</li>" for g in p["gates"] if not g["passed"]
    )
    return f"""<!doctype html><meta charset="utf-8"><title>FieldShift {e(decision_id)}</title>
<style>body{{font-family:sans-serif;max-width:1000px;margin:24px auto;padding:0 16px}}td,th{{border:1px solid #999;padding:6px;vertical-align:top}}table{{border-collapse:collapse}}</style>
<h1>Kế hoạch luân canh — {e(p["field_id"])}</h1><p>Lập ngày {e(p["as_of"])} · dữ liệu {e(p["versions"]["data"])} · kịch bản: lịch sử NASA POWER</p>
<table><tr><th>Phương án</th><th>Lịch vụ</th><th>Trạng thái</th><th>Tưới (trung vị)</th><th>Vì sao</th><th>Cần kiểm tra</th></tr>{rows}</table>
<h3>Giới hạn</h3><ul>{gates}</ul><p><b>{e(p["disclaimer"])}</b></p>"""
