"""Future Outlook & Scenario Builder (design v2 §6.3).

Optional forecast/projection inputs are normalized by adapters and injected by application.
Analog years keep real daily order (no shuffling).
"""

import calendar
import datetime as dt
import statistics as st

from fieldshift.domain.formatting import number_vi
from fieldshift.domain.models.scenario import ScenarioKind

# ENSO phases from NOAA ONI (°C). Analogs share the phase FAMILY (El Niño / neutral / La Niña):
# strength only labels the phase, otherwise a strong El Niño would have ~2 analogs in 2001–2025.
ENSO_STRONG_EL_NINO = 1.5
ENSO_EL_NINO = 0.5
ENSO_LA_NINA = -0.5
ENSO_STRONG_LA_NINA = -1.5
ENSO_MAX_ANALOGS = 5
ENSO_MIN_ANALOGS = 3
ENSO_SCENARIO_ID = "sc_enso_analog"
ENSO_EVIDENCE = ["ev_enso_oni", "ev_imerg_monthly", "ev_power_daily"]
DRY_SEASON_MONTHS = ((0, 12), (1, 1), (1, 2), (1, 3), (1, 4))  # (year offset, month): Dec–Apr
PHASE_VI = {
    "EL_NINO_STRONG": "El Niño mạnh",
    "EL_NINO": "El Niño",
    "NEUTRAL": "ENSO trung tính",
    "LA_NINA": "La Niña",
    "LA_NINA_STRONG": "La Niña mạnh",
}
DRIER_RATIO = 0.8  # analog/all dry-season rain below this -> "drier than normal" headline
WETTER_RATIO = 1.25


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


def enso_phase(value: float) -> str:
    if value >= ENSO_STRONG_EL_NINO:
        return "EL_NINO_STRONG"
    if value >= ENSO_EL_NINO:
        return "EL_NINO"
    if value <= ENSO_STRONG_LA_NINA:
        return "LA_NINA_STRONG"
    if value <= ENSO_LA_NINA:
        return "LA_NINA"
    return "NEUTRAL"


def phase_family(phase: str) -> str:
    return phase.removesuffix("_STRONG")


def enso_analogs(oni: dict, latest: tuple[int, int, float], as_of: dt.date, years) -> list[int]:
    """Start years Y (from `years`) whose ONI at the same centred month is in the same phase
    family as now, nearest |ONI_Y − ONI_now| first, at most ENSO_MAX_ANALOGS."""
    cy, cm, now = latest
    off, family = cy - as_of.year, phase_family(enso_phase(now))
    same = [
        y
        for y in years
        if (y + off, cm) in oni and phase_family(enso_phase(oni[(y + off, cm)])) == family
    ]
    return sorted(same, key=lambda y: (abs(oni[(y + off, cm)] - now), y))[:ENSO_MAX_ANALOGS]


def monthly_from_daily(weather: list[dict]) -> dict[tuple[int, int], float]:
    """Monthly rain totals for calendar months with every day present."""
    days, total = {}, {}
    for w in weather:
        k = (w["date"].year, w["date"].month)
        days[k] = days.get(k, 0) + 1
        total[k] = total.get(k, 0.0) + w["rain_mm"]
    return {k: v for k, v in total.items() if days[k] == calendar.monthrange(*k)[1]}


def season_rain_mm(monthly: dict, y: int, as_of: dt.date) -> float | None:
    """Dec(Y)–Apr(Y+1) total, only for seasons whose last month ended before as_of's month."""
    keys = [(y + dy, m) for dy, m in DRY_SEASON_MONTHS]
    if (y + 1, 4) >= (as_of.year, as_of.month) or any(k not in monthly for k in keys):
        return None
    return sum(monthly[k] for k in keys)


def season_label(y: int) -> str:
    return f"{y}–{(y + 1) % 100:02d}"


def year_outlook(ctx: dict, as_of: dt.date, years: list[int]) -> dict:
    """ENSO-conditioned analog years and their dry-season rain (association, not a forecast)."""
    enso = ctx.get("enso") or {}
    latest = enso.get("latest")
    out = {
        "status": "UNAVAILABLE",
        "reason": None,
        "enso": None,
        "analog_years": [],
        "analog_labels_vi": [],
        "dry_season_rain": {
            "analog_median_mm": None,
            "all_years_median_mm": None,
            "ratio": None,
            "sources": [],
        },
        "skill": {"correlation_r": None, "n_years": 0, "note_vi": ""},
        "headline_vi": "",
        "scenario_id": None,
        "evidence_ids": [],
    }
    if latest is None:
        return {**out, "reason": "ONI_NOT_AVAILABLE_AT_AS_OF"}
    oni = enso["oni"]
    cy, cm, value = latest
    phase = enso_phase(value)
    out["enso"] = {
        "index": "ONI",
        "centered_month": f"{cy}-{cm:02d}",
        "value": value,
        "phase": phase,
        "source": enso["source"],
    }
    analogs = enso_analogs(oni, latest, as_of, years)
    if len(analogs) < ENSO_MIN_ANALOGS:
        return {**out, "reason": "TOO_FEW_ANALOG_YEARS"}
    imerg = ctx.get("imerg_monthly")
    monthly = imerg or monthly_from_daily(ctx["weather"])
    sources = [enso["imerg_source"]] if imerg else []
    sources.append("NASA POWER PRECTOTCORR")  # analog members are simulated on POWER days
    rain = {
        y: r
        for y in range(as_of.year - 40, as_of.year)
        if (r := season_rain_mm(monthly, y, as_of)) is not None
    }
    analog_rain = [rain[y] for y in analogs if y in rain]
    a_med = round(st.median(analog_rain)) if analog_rain else None
    all_med = round(st.median(rain.values())) if rain else None
    ratio = round(a_med / all_med, 2) if a_med is not None and all_med else None
    off = cy - as_of.year
    pairs = [(oni[(y + off, cm)], r) for y, r in rain.items() if (y + off, cm) in oni]
    corr = round(st.correlation(*zip(*pairs)), 2) if len(pairs) >= ENSO_MIN_ANALOGS else None
    family = phase_family(phase)
    same = [
        y
        for y in rain
        if (y + off, cm) in oni and phase_family(enso_phase(oni[(y + off, cm)])) == family
    ]
    note = (
        f"Tín hiệu thống kê, không phải dự báo: tương quan ONI (tháng giữa {cm:02d}) với mưa "
        f"tháng 12–4 sau đó r = {number_vi(corr, 2) if corr is not None else 'chưa tính được'}"
        f" trên {number_vi(len(pairs))} năm."
    )
    if family != "NEUTRAL" and same:
        odd = max(same, key=rain.get) if family == "EL_NINO" else min(same, key=rain.get)
        note += (
            f" Năm {season_label(odd)} cũng {PHASE_VI[phase_family(phase)]} nhưng mưa mùa khô "
            f"{number_vi(round(rain[odd]))} mm."
        )
    labels = [season_label(y) for y in analogs]
    head = (
        f"Mùa khô {season_label(as_of.year)}: {PHASE_VI[phase]} "
        f"(ONI {'+' if value > 0 else ''}{number_vi(value, 1)}). Các năm tương tự "
        f"{', '.join(labels[:2])}…"
    )
    if ratio is None:
        head += " — chưa đủ dữ liệu mưa để so sánh."
    elif ratio < DRIER_RATIO:
        head += (
            f" mưa mùa khô chỉ khoảng {number_vi(round(ratio * 100))} % năm thường — nguy cơ hạn,"
            " mặn có thể cao hơn bình thường."
        )
        if family != "EL_NINO":
            head = head.split(" — nguy cơ")[0] + ". Tín hiệu thống kê mưa; chưa suy ra nguy cơ mặn."
    elif ratio > WETTER_RATIO:
        head += (
            f" mưa mùa khô khoảng {number_vi(round(ratio * 100))} % năm thường — mùa khô có thể"
            " bớt khắc nghiệt (vẫn phải đo mặn trước khi gieo)."
        )
    else:
        head += " mưa mùa khô gần như năm thường."
    head += " Tín hiệu thống kê, không phải dự báo."
    note += (
        " Hindcast: hướng mưa đúng 12/15 ca; chưa cho thấy lợi thế tưới của top-1 (0/15 ca giảm)."
    )
    return {
        **out,
        "status": "OK",
        "analog_years": analogs,
        "analog_labels_vi": labels,
        "dry_season_rain": {
            "analog_median_mm": a_med,
            "all_years_median_mm": all_med,
            "ratio": ratio,
            "sources": sources,
        },
        "skill": {"correlation_r": corr, "n_years": len(pairs), "note_vi": note},
        "headline_vi": head,
        "scenario_id": ENSO_SCENARIO_ID,
        "evidence_ids": list(ENSO_EVIDENCE),
    }


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
    for row in out:
        h = by_date[shift_year(row["date"], off)]
        forecast = (forecast_daily or {}).get(str(row["date"]), {})
        # SEAS5 has no POWER bias calibration: use its own Tmax for forecast days.
        row["heat_tmax"] = (
            row["tmax"]
            if "tmax" in forecast
            else h.get("heat_tmax", h["tmax"])
            + temp_delta
            + (monthly_tmax_delta or {}).get(str(row["date"].month), 0)
        )
    return out


def build_scenarios(
    ctx: dict,
    as_of: dt.date,
    span_days: int,
    override: dict | None = None,
    outlook: dict | None = None,
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
            "name": "Nóng hơn +1,5 °C",
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
    if outlook and outlook["status"] == "OK":
        enso = outlook["enso"]
        sc.append(
            {
                **base,
                "scenario_id": ENSO_SCENARIO_ID,
                "kind": "CLIMATOLOGY",
                "probability_semantics": "ANALOG_YEARS_CONDITIONED_ON_ENSO_NOT_FORECAST",
                "name": f"Năm tương tự (ENSO {PHASE_VI[enso['phase']]}: "
                + ", ".join(outlook["analog_labels_vi"])
                + ")",
                "evidence_ids": list(ENSO_EVIDENCE),
                "assumptions": [
                    f"analog_years_same_enso_phase_oni_{enso['centered_month']}",
                    "salinity_timing_from_plan_window_not_inferred_from_enso_alone",
                ],
                "members": [{"year": y} for y in outlook["analog_years"]],
            }
        )
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
