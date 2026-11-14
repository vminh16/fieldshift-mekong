"""Sinh docs/RULES.md từ mã nguồn + catalog (không viết tay): mọi luật, ngưỡng, nguồn, phân loại A/B/C.

Chạy: PYTHONPATH=apps/api/src python scripts/export_rules.py   (in hash nội dung)
Nguồn đọc-only: rotation_planner.py (regex trên source), crops.json, regions.json.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api/src"))

from fieldshift.domain.engines import rotation_planner as planner  # noqa: E402
from fieldshift.domain.catalog import CROPS, REGIONS  # noqa: E402

PLANNER_SRC = Path(planner.__file__)
OUT = ROOT / "docs/RULES.md"
A, B, C = "[A] tài liệu khoa học", "[B] heuristic nhóm tự đặt", "[C] trống/không hoạt động"

# Ý nghĩa + phân loại từng luật. Id/mức độ lấy từ source; một id mới chưa có ở đây sẽ hiện "chưa phân loại".
RULE_NOTES = {
    "R_WINDOW": ("Cây không thuộc lịch vụ của vùng (crops.allowed_windows)", A, "lịch MARD/Cục Trồng trọt (regions.json)"),
    "R_SEASON_OVERLAP": ("Thu hoạch + thời gian làm đất > ngày gieo vụ sau", A, "lịch vụ MARD; turnaround 10 ngày là giá trị vùng"),
    "R_DRAINAGE": ("Cây cạn cần thoát nước tốt nhưng nông dân báo thoát nước kém", B, "crops.requires_good_drainage do nhóm gán"),
    "R_DRAINAGE_UNKNOWN": ("Cây cạn cần thoát nước tốt, chưa xác nhận", B, "-"),
    "R_SALINITY": ("ECw đo được > ngưỡng ECw của cây (ECe≈1,5·ECw)", A, "FAO-29 / Maas-Hoffman 1977"),
    "R_SALINITY_UNKNOWN": ("Vụ trùng mùa mặn >= SALINITY_OVERLAP_DAYS ngày (tính cả mặn đến sớm SALINITY_EARLY_WEEKS tuần), chưa đo ECw", B, "ngưỡng ngày và 4 tuần do nhóm đặt; mùa mặn từ MARD/SIWRP"),
    "R_HEAT": ("Số ngày Tmax >= ngưỡng ở giai đoạn nhạy cảm (trung vị) >= HEAT_STRESS_DAYS_SOFT", B, "ngưỡng Tmax theo cây: xem bảng cây; ngưỡng ngày do nhóm đặt"),
    "R_WATER_STRESS": ("Số ngày thiếu nước (trung vị) >= WATER_STRESS_DAYS_SOFT", B, "ngưỡng ngày do nhóm đặt"),
    "R_WATERLOG": ("Cây cạn chịu úng kém và mưa trung vị trong vụ >= WATERLOG_RAIN_MM", B, "ngưỡng mm do nhóm đặt"),
    "R_MACHINERY": ("Cây cần máy (crops.machinery_required) khi no_new_machinery=True", None, "-"),
    "R_BUDGET": ("Cây chi phí 'high' khi budget_level='low'", B, "relative_cost_level do nhóm gán"),
    "R_PEST_CYCLE": ("Lúa liên tục các vụ (lợi ích luân canh định tính)", B, "định tính, không có số"),
    "R_UPSTREAM_DISCHARGE_LOW": ("Vùng ven biển + lưu lượng thượng nguồn thấp hơn nền cùng lịch", B, "GloFAS là tín hiệu vùng, không phải mặn"),
}
# (hằng số, giá trị literal trong field_rules nếu engine chưa export, mô tả)
CONSTANTS = [
    ("DEFAULT_CANAL_CAP_MM", None, "Trần tưới mỗi vụ cho 'canal_limited' (mm), giả định"),
    ("PPT_PER_DS_M", None, "TDS ≈ 640·ECw (FAO-29) -> ‰"),
    ("SCREENING_SCENARIOS", None, "Kịch bản dùng để sàng lọc"),
    ("HEAT_STRESS_DAYS_SOFT", 5, "R_HEAT: ngày"),
    ("WATER_STRESS_DAYS_SOFT", 7, "R_WATER_STRESS: ngày"),
    ("WATERLOG_RAIN_MM", 600, "R_WATERLOG: mm mưa/vụ"),
    ("SALINITY_OVERLAP_DAYS", 7, "R_SALINITY*: ngày trùng mùa mặn"),
    ("SALINITY_EARLY_WEEKS", -4, "R_SALINITY*: mặn đến sớm (tuần, âm = sớm)"),
]


def planner_rules() -> list[tuple[str, str]]:
    """(rule_id, severity) parsed from the planner source, first occurrence order."""
    src = PLANNER_SRC.read_text(encoding="utf-8")
    seen = {}
    for rid, sev in re.findall(r'"(R_[A-Z_]+)",\s*"(HARD|SOFT|UNKNOWN_REQUIRES_CHECK)"', src):
        seen.setdefault(rid, sev)
    return list(seen.items())


def has(text_list, *words):
    return any(w.lower() in t.lower() for t in text_list for w in words)


def crop_class(c):
    """Phân loại từng nhóm tham số của cây dựa trên sources/limitations của chính cây đó."""
    src, lim = c["sources"], c["limitations"]
    placeholder = c["water_regime"] == "none"
    # a single limitation line must be both about salinity and say "estimate/uncertain/lower-confidence"
    vague = lambda *w: any(  # noqa: E731
        has([t], "estimate", "uncertain", "lower-confidence") and has([t], *w) for t in lim
    )
    return {
        "kc": B if placeholder else (A if has(src, "FAO-56 Table 12") else B),
        "salinity": C if placeholder else (B if vague("salinity", "threshold") else A if has(src, "FAO-29", "Maas") else B),
        "heat": C if placeholder else (A if "Satake" in c["heat"]["note"] else B),
        "duration": A if has(src, "OM5451", "varieties") else B,
        "windows": A if c["id"] == "rice" else B,
        "machinery": A if c["machinery_required"] and src else C if not c["machinery_required"] else B,
    }


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(x).replace("|", "/") for x in r) + " |" for r in rows]
    return "\n".join(out)


def build() -> tuple[str, str]:
    parts = ["# Luật, ngưỡng và nguồn của FieldShift-Mekong\n"]
    parts.append(
        "> Tệp này được SINH TỰ ĐỘNG bởi `scripts/export_rules.py` (không sửa tay). Phân loại: "
        f"**{A}** = có trích dẫn; **{B}** = ngưỡng/giá trị nhóm tự đặt, chưa có nguồn; "
        f"**{C}** = tham số trống hoặc luật không bao giờ kích hoạt.\n"
    )
    mech_live = any(c["machinery_required"] for c in CROPS["crops"])
    parsed = planner_rules()

    rows = []
    for rid, sev in parsed:
        desc, cls, note = RULE_NOTES.get(rid, ("(chưa mô tả)", "chưa phân loại", "-"))
        if rid == "R_MACHINERY":
            cls = B if mech_live else C
            note = "Có cây cần máy" if mech_live else "KHÔNG HOẠT ĐỘNG: machinery_required rỗng ở mọi cây -> luật HARD không bao giờ bắn (AC-07 chỉ test trên catalog giả lập)"
        rows.append((rid, sev, desc, cls, note))
    parts += ["## 1. Luật của engine (parse từ `rotation_planner.py`)\n", table(["Rule", "Mức", "Điều kiện", "Phân loại", "Nguồn / ghi chú"], rows), ""]

    rows = []
    for name, literal, desc in CONSTANTS:
        if hasattr(planner, name):
            val, where, cls = getattr(planner, name), "hằng số module", A if name == "PPT_PER_DS_M" else B
            val = sorted(val) if isinstance(val, frozenset) else val
        else:
            val, where, cls = literal if literal is not None else "?", "literal trong field_rules (chưa export)", B
        rows.append((name, val, where, cls, desc))
    parts += ["## 2. Hằng số module\n", table(["Tên", "Giá trị", "Vị trí", "Phân loại", "Ý nghĩa"], rows), ""]

    rows, notes = [], []
    for c in CROPS["crops"]:
        k = crop_class(c)
        rows.append((
            c["id"],
            f"{c['kc']['ini']}/{c['kc']['mid']}/{c['kc']['end']} {k['kc'][:3]}",
            f"{c['salinity']['ece_threshold_ds_m']} dS/m, {c['salinity']['slope_pct_per_ds_m']}%/dS/m; ECw {c['salinity']['ecw_threshold_ds_m']} {k['salinity'][:3]}",
            f"{c['heat']['tmax_threshold_c']} °C {k['heat'][:3]}",
            f"{c['duration_days']['min']}/{c['duration_days']['typical']}/{c['duration_days']['max']} {k['duration'][:3]}",
            f"{', '.join(c['allowed_windows'])} {k['windows'][:3]}",
            f"{c['machinery_required'] or 'rỗng'} {k['machinery'][:3]}",
        ))
        notes.append(f"**{c['id']}** — nguồn: " + "; ".join(c["sources"]) + ". Hạn chế: " + " | ".join(c["limitations"]))
    parts += [
        f"## 3. Tham số cây trồng (`crops.json` {CROPS['version']})\n",
        table(["Cây", "Kc ini/mid/end", "Mặn ECe ngưỡng, độ dốc; ECw", "Ngưỡng Tmax", "Thời gian ngày min/typ/max", "Cửa sổ", "Máy móc"], rows),
        "\nMã trong ô: [A]/[B]/[C] như trên.\n",
        "### Nguồn và hạn chế theo cây\n",
        *[f"- {n}" for n in notes],
        "",
    ]

    rows = []
    for reg in REGIONS.values():
        p, s, sal = reg["paddy"], reg["soil_prior"], reg["salinity_season"]
        for label, val, blk in [
            ("Cửa sổ vụ", "; ".join(f"{w['id']} {w['sow_from']}→{w['sow_to']}" for w in reg["season_windows"]), reg),
            ("min_turnaround_days", reg["min_turnaround_days"], reg),
            ("Paddy: thấm / làm đất / ponding", f"{p['percolation_mm_day']} mm/ngày / {p['land_prep_mm']} mm / {p['target_ponding_mm']}-{p['max_ponding_mm']} mm", p),
            ("Đất: TAW / pH / kết cấu", f"{s['taw_mm_per_m']} mm/m / {s['ph_range']} / {s['texture']}", s),
            ("Mùa mặn: đầu / đỉnh / cuối", f"{sal['typical_onset']} / {sal['peak']} / {sal['typical_end']}", sal),
        ]:
            rows.append((reg["id"], label, val, A if blk.get("sources") else B, "; ".join(blk.get("sources", [])) or "-", " | ".join(blk.get("limitations", [])) or "-"))
    parts += [
        f"## 4. Giá trị vùng (`regions.json` {json.loads((ROOT / 'apps/api/src/fieldshift/resources/regions.json').read_text())['version']})\n",
        table(["Vùng", "Tham số", "Giá trị", "Phân loại", "Nguồn", "Hạn chế"], rows),
        "",
    ]

    body = "\n".join(parts)
    digest = hashlib.sha256(body.encode()).hexdigest()[:16]
    return body + f"\n---\nHash nội dung (sha256, 16 ký tự đầu, không gồm dòng này): `{digest}`\n", digest


def main() -> None:
    text, digest = build()
    OUT.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}  rules={len(planner_rules())}  hash={digest}")


if __name__ == "__main__":
    main()
