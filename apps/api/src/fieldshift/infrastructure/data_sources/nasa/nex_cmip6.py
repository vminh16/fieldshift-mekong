"""Read processed NEX-GDDP-CMIP6 v2 monthly point series; no heavy NetCDF runtime."""

import json
import math
from pathlib import Path
from statistics import mean

RESOURCES = Path(__file__).resolve().parents[3] / "resources" / "projections"


def load_projections(cache_key: str | None) -> tuple[list[dict], list[str]]:
    path = RESOURCES / f"{cache_key}.json"
    if not path.exists():
        return [], ["NEX-GDDP-CMIP6: no processed projection series for this site."]
    data = json.loads(path.read_text())
    series = {(s["model"], s["scenario"], s["variable"]): s for s in data["series"]}
    out, notes = [], []
    for model, ssp in sorted({(m, s) for m, s, _ in series}):
        deltas = {}
        for variable in ("tasmax", "pr"):
            s = series.get((model, ssp, variable), {})
            if s.get("unit") != ("degC" if variable == "tasmax" else "mm/month"):
                break
            values = {v["month"]: v["value"] for v in s["values"]}
            monthly = {}
            for month in range(1, 13):
                keys = [f"{y}-{month:02d}" for y in [*range(2025, 2035), *range(2041, 2051)]]
                if not all(
                    k in values and isinstance(values[k], (int, float)) and math.isfinite(values[k])
                    for k in keys
                ):
                    break
                base, future = (
                    mean(values[k] for k in keys[:10]),
                    mean(values[k] for k in keys[10:]),
                )
                if variable == "pr" and (base <= 0 or future < 0):
                    break
                monthly[str(month)] = future - base if variable == "tasmax" else future / base
            if len(monthly) != 12:
                break
            deltas[variable] = monthly
        if len(deltas) != 2:
            notes.append(
                f"NEX-GDDP-CMIP6 {model}/{ssp}: skipped; complete 2025–2034 and 2041–2050 monthly tasmax/pr required."
            )
            continue
        out.append(
            {
                "model": model,
                "ssp": ssp,
                "monthly_tmax_delta": deltas["tasmax"],
                "monthly_rain_factor": deltas["pr"],
                "version": data["version"],
            }
        )
    return out, notes
