"""Độ nhạy của kết quả engine với các tham số chưa có nguồn -> docs/SENSITIVITY_REPORT.md.

Chạy offline trên cache có sẵn: PYTHONPATH=apps/api/src python scripts/sensitivity.py
Mỗi lần chỉ đổi MỘT tham số, trong bộ nhớ (deep-copy + khôi phục); không ghi file tài nguyên.
Gọi engine qua chính endpoint POST /v1/plans (TestClient), cùng đường đi với API.
"""

import copy
import datetime as dt
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api/src"))
os.environ["FIELDSHIFT_DATA_DIR"] = tempfile.mkdtemp(prefix="sens-")

import httpx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from fieldshift.domain.catalog import CROP_BY_ID, REGIONS  # noqa: E402
from fieldshift.domain.engines import rotation_planner as planner  # noqa: E402
from fieldshift.infrastructure.data_sources import glofas  # noqa: E402
from fieldshift.infrastructure.data_sources.forecasts import open_meteo_seasonal  # noqa: E402
from fieldshift.main import app  # noqa: E402

AS_OF = "2026-11-14"
FIELDS = {"fld_cantho": "Cần Thơ", "fld_chaudoc": "Châu Đốc", "fld_bentre": "Bến Tre", "fld_soctrang": "Sóc Trăng"}
OUT = ROOT / "docs/SENSITIVITY_REPORT.md"
FLAG = 0.20


def go_offline():
    """Same frozen clock + no network as tests/conftest.py (bundled caches only)."""

    class D(dt.date):
        @classmethod
        def today(cls):
            return cls(2026, 11, 13)

    class T(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            i = cls(2026, 11, 13, 14, tzinfo=dt.timezone.utc)
            return i.astimezone(tz) if tz else i.replace(tzinfo=None)

    clock = SimpleNamespace(date=D, datetime=T, timezone=dt.timezone, timedelta=dt.timedelta)
    glofas.dt = clock
    open_meteo_seasonal.dt = clock

    def refuse(*a, **k):
        raise httpx.ConnectError("sensitivity.py runs offline")

    httpx.get = refuse


# ---- perturbations: (parameter, value label, setter(ctx manager)) ----
@contextmanager
def region_value(path, value):
    block = REGIONS["mekong"]
    for k in path[:-1]:
        block = block[k]
    old = block[path[-1]]
    block[path[-1]] = value
    try:
        yield
    finally:
        block[path[-1]] = old


@contextmanager
def kc_scale(f):
    saved = copy.deepcopy({c: v["kc"] for c, v in CROP_BY_ID.items()})
    for v in CROP_BY_ID.values():
        v["kc"] = {k: x * f for k, x in v["kc"].items()}
    try:
        yield
    finally:
        for c, kc in saved.items():
            CROP_BY_ID[c]["kc"] = kc


@contextmanager
def constant(name, value):
    old = getattr(planner, name)
    setattr(planner, name, value)
    try:
        yield
    finally:
        setattr(planner, name, old)


def perturbations():
    out = []
    for v in (1, 2, 5):
        out.append(("Thấm paddy (mm/ngày)", f"{v}", lambda v=v: region_value(("paddy", "percolation_mm_day"), float(v))))
    for v in (120, 150, 200):
        out.append(("TAW đất (mm/m)", f"{v}", lambda v=v: region_value(("soil_prior", "taw_mm_per_m"), float(v))))
    for f in (0.9, 1.0, 1.1):
        out.append(("Kc mọi cây", f"×{f}", lambda f=f: kc_scale(f)))
    for name, label, vals in (
        ("HEAT_STRESS_DAYS_SOFT", "Ngưỡng ngày nóng (R_HEAT)", (3, 5, 10)),
        ("WATER_STRESS_DAYS_SOFT", "Ngưỡng ngày thiếu nước (R_WATER_STRESS)", (5, 7, 14)),
        ("WATERLOG_RAIN_MM", "Ngưỡng mưa úng (mm/vụ)", (400, 600, 800)),
    ):
        for v in vals:
            out.append((label, f"{v}", (lambda n=name, v=v: constant(n, v)) if hasattr(planner, name) else None))
    return out


def run(client, fid):
    r = client.post("/v1/plans", json={"field_id": fid, "as_of": AS_OF})
    assert r.status_code == 201, r.text
    p = r.json()
    opts = [o["sequence_id"] for o in p["options"]]
    return {
        "ids": opts,
        "status": {o["sequence_id"]: o["decision_status"] for o in [p["baseline"], *p["options"]]},
        "base_irr": p["baseline"]["metrics"]["sc_clim"]["irrigation_need"]["value"],
    }


def compare(ref, new):
    union = set(ref["ids"]) | set(new["ids"])
    jac = len(set(ref["ids"]) & set(new["ids"])) / len(union) if union else 1.0
    changed = [k for k in ref["status"].keys() & new["status"].keys() if ref["status"][k] != new["status"][k]]
    d_irr = None
    if ref["base_irr"]:
        d_irr = (new["base_irr"] - ref["base_irr"]) / ref["base_irr"] * 100
    return {
        "top1_same": bool(ref["ids"]) and ref["ids"][:1] == new["ids"][:1],
        "jaccard": jac,
        "status_changes": len(changed),
        "d_irr": d_irr,
    }


def main() -> None:
    go_offline()
    rows, byparam = [], {}
    with TestClient(app) as client:
        refs = {f: run(client, f) for f in FIELDS}
        again = {f: run(client, f) for f in FIELDS}
        deterministic = refs == again
        for param, label, mk in perturbations():
            if mk is None:
                rows.append((param, label, None))
                continue
            for fid in FIELDS:
                with mk():
                    res = compare(refs[fid], run(client, fid))
                rows.append((param, label, (fid, res)))
                byparam.setdefault(param, []).append(res)

    L = ["# Báo cáo độ nhạy (sensitivity)\n"]
    L.append(
        f"Sinh tự động bởi `scripts/sensitivity.py`. as_of `{AS_OF}`, offline trên cache có sẵn, yêu cầu mặc định "
        "(horizon 3 vụ, ràng buộc mặc định, outlook CLIMATOLOGY+STRESS_TEST). Mỗi lần đổi MỘT tham số trong bộ nhớ.\n"
    )
    L.append(
        "- **Top-1**: phương án đầu tiên trong `options` (thứ tự theo ưu tiên mặc định) so với tham chiếu.\n"
        "- **Jaccard**: |giao|/|hợp| của tập `sequence_id` trong shortlist so với tham chiếu.\n"
        "- **Đổi status**: số chuỗi có mặt ở cả hai lần chạy nhưng `decision_status` đổi.\n"
        "- **ΔIrr**: thay đổi % nhu cầu tưới của baseline (kịch bản khí hậu).\n"
        f"- **Cờ `cần nguồn`**: tham số mà tỷ lệ (ruộng × giá trị) đổi top-1 **hoặc** shortlist (Jaccard<1) > {FLAG:.0%}, "
        f"hoặc làm đổi nhu cầu tưới baseline > {FLAG:.0%}.\n"
    )
    L.append(f"Kiểm tra xác định: chạy tham chiếu 2 lần cho kết quả {'GIỐNG HỆT' if deterministic else 'KHÁC NHAU (đáng ngờ)'}.\n")
    L.append("## Kết quả chi tiết\n")
    L.append("| Tham số | Giá trị | Ruộng | Top-1 giữ nguyên | Jaccard | Đổi status | ΔIrr baseline |")
    L.append("|---|---|---|---|---|---|---|")
    for param, label, r in rows:
        if r is None:
            L.append(f"| {param} | {label} | * | chưa exposed | - | - | - |")
        else:
            fid, x = r
            d = "-" if x["d_irr"] is None else f"{x['d_irr']:+.1f}%"
            L.append(f"| {param} | {label} | {FIELDS[fid]} | {'có' if x['top1_same'] else 'KHÔNG'} | {x['jaccard']:.2f} | {x['status_changes']} | {d} |")
    L.append("\n## Tóm tắt theo tham số\n")
    L.append("| Tham số | Số ca | Đổi top-1 | Đổi shortlist | Đổi status | Max abs ΔIrr baseline | Kết luận |")
    L.append("|---|---|---|---|---|---|---|")
    flagged, magnitude = [], []
    for param, rs in byparam.items():
        n = len(rs)
        t = sum(not x["top1_same"] for x in rs) / n
        s = sum(x["jaccard"] < 1 for x in rs) / n
        st = sum(x["status_changes"] > 0 for x in rs) / n
        mx = max((abs(x["d_irr"]) for x in rs if x["d_irr"] is not None), default=0)
        flag, big = max(t, s) > FLAG, mx > FLAG * 100
        if flag:
            flagged.append(param)
        if big:
            magnitude.append(param)
        verdict = ("**cần nguồn** (xếp hạng/shortlist đổi)" if flag else "thứ hạng ổn định") + (
            "; **cần nguồn** (độ lớn nhu cầu tưới đổi > 20%)" if big else ""
        )
        L.append(f"| {param} | {n} | {t:.0%} | {s:.0%} | {st:.0%} | {mx:.1f}% | {verdict} |")
    missing = sorted({p for p, _, r in rows if r is None})
    for p in missing:
        L.append(f"| {p} | 0 | - | - | - | - | chưa exposed — chạy lại sau khi merge nhánh engine |")
    L.append("\n## Kết luận\n")
    L.append("- Tham số làm đổi kết quả > 20%: " + (", ".join(flagged) if flagged else "không có") + ".")
    L.append("- Tham số làm đổi độ lớn nhu cầu tưới baseline > 20% (số tuyệt đối không nên trích như đo đạc): " + (", ".join(magnitude) if magnitude else "không có") + ".")
    if missing:
        L.append("- Chưa kiểm được (hằng số còn là literal trong `field_rules`, chưa exposed): " + "; ".join(missing) + ". Chạy lại script sau khi merge nhánh engine.")
    L.append("- Mẫu nhỏ: 4 ruộng demo, 1 ngày as_of, 1 yêu cầu mặc định; đây là kiểm tra độ nhạy, không phải xác nhận mô hình.")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}; flagged={flagged}; magnitude={magnitude}; not_exposed={missing}; deterministic={deterministic}")


if __name__ == "__main__":
    main()
