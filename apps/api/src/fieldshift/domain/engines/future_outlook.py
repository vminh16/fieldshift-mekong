"""Future Outlook & Scenario Builder (design v2 §6.3).

Optional forecast/projection inputs are normalized by adapters and injected by application.
Analog years keep real daily order (no shuffling).
"""

import datetime as dt

from fieldshift.domain.models.scenario import ScenarioKind


def shift_year(d: dt.date, years: int) -> dt.date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:  # Feb 29 -> Feb 28
        return d.replace(year=d.year + years, day=28)


def analog_years(ctx: dict, as_of: dt.date, span_days: int) -> list[int]:
    """Historical start years Y whose shifted horizon lies fully inside the record (< as_of)."""
    dates = {w["date"] for w in ctx["weather"]}
    out = []
    for y in range(as_of.year - 40, as_of.year):
        off = y - as_of.year
        if (
            all(
                shift_year(as_of + dt.timedelta(days=i), off) in dates
                for i in range(0, span_days, 7)
            )
            and shift_year(as_of + dt.timedelta(days=span_days), off) in dates
        ):
            out.append(y)
    return out


def dry_season_rain(ctx: dict, as_of: dt.date, y: int) -> float:
    """Dec(Y)–Apr(Y+1) rain, i.e. the dry season inside the analog horizon."""
    return sum(
        w["rain_mm"]
        for w in ctx["weather"]
        if (w["date"].year == y and w["date"].month == 12)
        or (w["date"].year == y + 1 and w["date"].month <= 4)
    )


def build_weather(
    ctx: dict,
    as_of: dt.date,
    span_days: int,
    year: int,
    temp_delta: float = 0.0,
    rain_factor: float = 1.0,
    monthly_tmax_delta: dict | None = None,
    monthly_rain_factor: dict | None = None,
    forecast_daily: dict | None = None,
) -> list[dict]:
    by_date = {w["date"]: w for w in ctx["weather"]}
    off = year - as_of.year
    out = []
    for i in range(span_days + 1):
        d = as_of + dt.timedelta(days=i)
        h = by_date.get(shift_year(d, off))
        if h is None:
            continue
        out.append(
            {
                **h,
                "date": d,
                "tmax": h["tmax"] + temp_delta + (monthly_tmax_delta or {}).get(str(d.month), 0),
                "tmin": h["tmin"] + temp_delta,
                "tdew": h["tdew"] + temp_delta,
                "rain_mm": h["rain_mm"]
                * rain_factor
                * (monthly_rain_factor or {}).get(str(d.month), 1),
                **((forecast_daily or {}).get(str(d), {}) if i < 180 else {}),
            }
        )
    return out


def build_scenarios(
    ctx: dict, as_of: dt.date, span_days: int, override: dict | None = None
) -> list[dict]:
    years = analog_years(ctx, as_of, span_days)
    if not years:
        return []
    dry = sorted(years, key=lambda y: dry_season_rain(ctx, as_of, y))[:3]
    wet = max(years, key=lambda y: dry_season_rain(ctx, as_of, y))
    base = {"probability": None, "evidence_ids": ["ev_power_daily"], "salinity_shift_weeks": 0}
    sc = [
        {
            **base,
            "scenario_id": "sc_clim",
            "kind": "CLIMATOLOGY",
            "probability_semantics": "HISTORICAL_DISTRIBUTION_NOT_FORECAST",
            "name": f"Lịch sử {years[0]}–{years[-1] + 1} ({len(years)} năm)",
            "assumptions": ["future_resembles_past_distribution"],
            "members": [{"year": y} for y in years],
        },
        {
            **base,
            "scenario_id": "sc_dry",
            "kind": "STRESS_TEST",
            "probability_semantics": "NONE_ASSUMPTION",
            "name": "Mùa khô như các năm khô nhất (" + ", ".join(f"{y}–{y + 1}" for y in dry) + ")",
            "assumptions": [f"analog_dry_season_{y}_{y + 1}" for y in dry],
            "members": [{"year": y} for y in dry],
        },
        {
            **base,
            "scenario_id": "sc_hot",
            "kind": "STRESS_TEST",
            "probability_semantics": "NONE_ASSUMPTION",
            "name": "Nóng hơn +1.5 °C",
            "assumptions": ["tmax_tmin_tdew_plus_1.5C"],
            "members": [{"year": y, "temp_delta": 1.5} for y in years],
        },
        {
            **base,
            "scenario_id": "sc_rain_minus30",
            "kind": "STRESS_TEST",
            "probability_semantics": "NONE_ASSUMPTION",
            "name": "Mưa giảm 30 %",
            "assumptions": ["rain_x0.7"],
            "members": [{"year": y, "rain_factor": 0.7} for y in years],
        },
        {
            **base,
            "scenario_id": "sc_salt_early",
            "kind": "STRESS_TEST",
            "probability_semantics": "NONE_ASSUMPTION",
            "name": "Mặn đến sớm 4 tuần",
            "assumptions": ["salinity_onset_minus_4_weeks_user_defined"],
            "salinity_shift_weeks": -4,
            "evidence_ids": ["ev_salinity_season"],
            "members": [{"year": y} for y in years],
        },
        {
            **base,
            "scenario_id": "sc_wet_ref",
            "kind": "CLIMATOLOGY",
            "probability_semantics": "HISTORICAL_DISTRIBUTION_NOT_FORECAST",
            "name": f"Năm mùa khô ướt nhất ({wet}–{wet + 1})",
            "assumptions": [f"analog_year_{wet}"],
            "members": [{"year": wet}],
        },
    ]
    if override:
        sc.append(
            {
                **base,
                "scenario_id": "sc_whatif",
                "kind": "STRESS_TEST",
                "probability_semantics": "NONE_ASSUMPTION",
                "origin": "user_what_if",
                "name": "Tình huống người dùng đặt",
                "assumptions": [f"{k}={v}" for k, v in override.items() if v not in (None, {}, 0)],
                "salinity_shift_weeks": override.get("salinity_onset_shift_weeks") or 0,
                "members": [
                    {
                        "year": y,
                        "temp_delta": override.get("temp_delta_c") or 0.0,
                        "rain_factor": 1 + (override.get("rain_delta_pct") or 0) / 100,
                    }
                    for y in years
                ],
            }
        )
    forecast = ctx.get("forecast")
    if forecast and 0 <= (as_of - dt.date.fromisoformat(forecast["issue_time"][:10])).days <= 35:
        sc.append(
            {
                **base,
                "scenario_id": "sc_forecast",
                "kind": ScenarioKind.FORECAST,
                "name": "ECMWF SEAS5 seasonal ensemble",
                "source": forecast["source"],
                "issue_time": forecast["issue_time"],
                "available_at": forecast["available_at"],
                "quality_flags": forecast["quality_flags"],
                "omitted_member_ids": forecast.get("omitted_member_ids", []),
                "ensemble_member_ids": [m["member_id"] for m in forecast["members"]],
                "forecast_window": [str(as_of), min(max(m["daily"]) for m in forecast["members"])],
                "probability_semantics": "ensemble members, skill not evaluated for Mekong",
                "evidence_ids": ["ev_seasonal_forecast", "ev_power_daily"],
                "assumptions": [
                    "First up to 180 days use SEAS5 Tmax/Tmin/rain ensemble members; remaining horizon spliced onto POWER climatology analog years.",
                    "Dew point, radiation and wind needed by FAO-56 come from the same analog-year day throughout; cross-variable coherence is approximate.",
                    "Members paired deterministically with cycling analog years; no evaluated skill or calibrated probabilities.",
                ],
                "members": [
                    {"year": years[i % len(years)], **m} for i, m in enumerate(forecast["members"])
                ],
            }
        )
    for projection in ctx.get("projections", []):
        model, ssp = projection["model"], projection["ssp"]
        sc.append(
            {
                **base,
                "scenario_id": f"sc_proj_{model}_{ssp}",
                "kind": ScenarioKind.CLIMATE_PROJECTION,
                "name": f"NEX-GDDP-CMIP6 {model} {ssp}",
                "model": model,
                "ssp": ssp,
                "source": "NASA NEX-GDDP-CMIP6 v2.0",
                "issue_time": None,
                "probability_semantics": "SSP pathways, no assigned probabilities",
                "evidence_ids": ["ev_nex_cmip6", "ev_power_daily"],
                "quality_flags": ["MONTHLY_DELTA_METHOD", "NOT_WEATHER_FORECAST"],
                "assumptions": [
                    "Monthly Tmax delta: mean 2041–2050 minus mean 2025–2034; precipitation multiplied by monthly future/base ratio.",
                    "Applied to POWER analog-year days as a long-term sensitivity scenario; not predictions for the planning dates.",
                    "Tmin, dew point, radiation and wind remain from the analog-year day (tasmax/pr only).",
                ],
                "monthly_tmax_delta": projection["monthly_tmax_delta"],
                "monthly_rain_factor": projection["monthly_rain_factor"],
                "members": [
                    {
                        "year": y,
                        **{k: projection[k] for k in ("monthly_tmax_delta", "monthly_rain_factor")},
                    }
                    for y in years
                ],
            }
        )
    for s in sc:
        s.setdefault("as_of", str(as_of))
        s["representative_year"] = s["members"][len(s["members"]) // 2]["year"]
    return sc
