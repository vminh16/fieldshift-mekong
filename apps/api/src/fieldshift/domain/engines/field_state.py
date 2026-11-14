"""Field State Estimator (design v2 §6.2): FieldProfile + FieldContext -> InitialFieldState at as_of."""

import datetime as dt
import statistics as st

from fieldshift.domain.value_objects.measure import measure


def climate_summary(weather: list[dict]) -> dict:
    """Monthly means over full years in the record (for /context)."""
    by_ym: dict[tuple, list] = {}
    for w in weather:
        by_ym.setdefault((w["date"].year, w["date"].month), []).append(w)
    years = sorted({y for y, _ in by_ym})
    full = [y for y in years if sum(len(by_ym.get((y, m), [])) for m in range(1, 13)) >= 360]
    rain = {m: [] for m in range(1, 13)}
    tmax = {m: [] for m in range(1, 13)}
    hot = {m: 0 for m in range(1, 13)}
    for y in full:
        for m in range(1, 13):
            rows = by_ym.get((y, m), [])
            rain[m].append(sum(w["rain_mm"] for w in rows))
            tmax[m] += [w["tmax"] for w in rows]
            hot[m] += sum(1 for w in rows if w["tmax"] >= 35)
    n = len(full) or 1
    return {
        "years": [full[0], full[-1]] if full else None,
        "monthly": [
            {
                "month": m,
                "rain_mm": round(st.mean(rain[m]), 1) if rain[m] else None,
                "tmax_c": round(st.mean(tmax[m]), 1) if tmax[m] else None,
                "days_tmax_ge_35": round(hot[m] / n, 1),
            }
            for m in range(1, 13)
        ],
        "evidence_ids": ["ev_power_daily"],
    }


def estimate_state(field: dict, ctx: dict, as_of: dt.date, observations: list[dict]) -> dict:
    """InitialFieldState: every variable tagged by origin. Unknown stays unknown (§6.2)."""
    prof = field["profile"]
    latest = {}
    for o in sorted(observations, key=lambda o: o["observed_at"]):
        if o["observed_at"] <= str(as_of):
            latest[o["variable"]] = o
    g = ctx["gwet"]
    recent = [v for d, v in g.items() if as_of - dt.timedelta(days=30) <= d]
    same = [
        v
        for d, v in g.items()
        if d.year < as_of.year and abs((d.replace(year=2000) - as_of.replace(year=2000)).days) <= 15
    ]
    gw = round(st.mean(recent), 3) if recent else None
    anomaly = round(gw - st.mean(same), 3) if gw is not None and same else None

    upstream = ctx.get("upstream_discharge", {})
    ecw = latest.get("canal_ecw")
    drainage = latest.get("drainage")
    drainage_val = drainage["value_text"] if drainage else prof.get("drainage") or "unknown"
    irrigation = prof.get("irrigation")
    return {
        "as_of": str(as_of),
        "upstream_discharge": measure(
            upstream.get("value"),
            "m³/s",
            "estimated_from_regional_data",
            "Ước lượng vùng",
            ["ev_glofas"],
            reason=upstream.get("reason") or "GLOFAS_UNAVAILABLE",
        )
        | {"date": upstream.get("date"), "context_only": True},
        "upstream_discharge_anomaly": measure(
            upstream.get("anomaly_pct"),
            "%",
            "estimated_from_regional_data",
            "Ước lượng vùng",
            ["ev_glofas"],
            reason="SAME_CALENDAR_CLIMATOLOGY_UNAVAILABLE",
        ),
        "upstream_discharge_trend": measure(
            upstream.get("trend_m3_s_per_day"),
            "m³/s/day",
            "estimated_from_regional_data",
            "Ước lượng vùng",
            ["ev_glofas"],
            reason="DISCHARGE_TREND_UNAVAILABLE",
        ),
        "root_zone_wetness": measure(
            gw, "fraction_0_1", "estimated_from_regional_data", "Ước lượng vùng", ["ev_power_gwet"]
        ),
        "root_zone_wetness_anomaly": measure(
            anomaly,
            "fraction_0_1",
            "estimated_from_regional_data",
            "Ước lượng vùng",
            ["ev_power_gwet"],
        ),
        "initial_depletion_frac": measure(
            round(min(0.9, max(0.0, 1 - gw)), 2) if gw is not None else 0.3,
            "fraction_TAW",
            "inferred_by_model",
            "Dự kiến",
            ["ev_power_gwet"],
        ),
        "canal_ecw": (
            measure(
                ecw["value"],
                "dS/m",
                "measured_at_field"
                if ecw["evidence_kind"] == "OBSERVED_FIELD"
                else "reported_by_farmer",
                "Đo tại ruộng",
                [f"obs:{ecw['id']}"],
            )
            if ecw
            else measure(None, "dS/m", "unknown", "Chưa biết", reason="CANAL_ECW_NOT_MEASURED")
        ),
        "drainage": {
            "value": drainage_val,
            "origin": "reported_by_farmer" if drainage_val != "unknown" else "unknown",
            "label": "Nông dân khai báo" if drainage_val != "unknown" else "Chưa biết",
        },
        # Missing irrigation is computed as "full" (planner default) but must not read as farmer-reported.
        "irrigation": {"value": irrigation, "origin": "reported_by_farmer"}
        if irrigation
        else {"value": "full", "origin": "assumed_default", "label": "Giả định mặc định"},
        "coastal_salinity_risk": {
            "value": bool(prof.get("coastal_salinity_risk")),
            "origin": "regional_config",
            "evidence_ids": ["ev_salinity_season"],
        },
        "elevation_m": measure(
            ctx["elevation_m"], "m", "estimated_from_regional_data", "Ước lượng vùng", ["ev_srtm"]
        ),
        "soil": {**ctx["soil"], "evidence_ids": ["ev_soil"]},
        "crop_history": prof.get("history", []),
        "data_last_date": str(ctx["last_data_date"]),
    }
