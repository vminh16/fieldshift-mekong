"""Future Outlook & Scenario Builder (design v2 §6.3).

No verified seasonal forecast and NASA POWER Projection returns fill values for Asia (tested 2026-11-13),
so the set is CLIMATOLOGY + STRESS_TEST. Analog years keep real daily order (no shuffling).
"""

import datetime as dt


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
                "tmax": h["tmax"] + temp_delta,
                "tmin": h["tmin"] + temp_delta,
                "tdew": h["tdew"] + temp_delta,
                "rain_mm": h["rain_mm"] * rain_factor,
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
    for s in sc:
        s["representative_year"] = s["members"][len(s["members"]) // 2]["year"]
    return sc
