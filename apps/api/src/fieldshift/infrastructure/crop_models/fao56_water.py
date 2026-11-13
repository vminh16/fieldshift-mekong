"""Crop water balance for the Mekong Delta rotation tool (FAO-56, Allen et al. 1998).

Units: temperatures degC, radiation MJ m-2 day-1, wind m/s at 2 m, water mm, pressure kPa.
"""

import datetime
import math

_GSC = 0.0820  # solar constant, MJ m-2 min-1
_SIGMA = 4.903e-9  # Stefan-Boltzmann, MJ K-4 m-2 day-1


def _es(t: float) -> float:
    """Saturation vapour pressure, kPa (FAO-56 Eq. 11)."""
    return 0.6108 * math.exp(17.27 * t / (t + 237.3))


def _ra(doy: int, lat_deg: float) -> float:
    """Extraterrestrial radiation, MJ m-2 day-1 (FAO-56 Eq. 21-25)."""
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)  # Eq. 23
    delta = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)  # Eq. 24
    x = max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta)))
    ws = math.acos(x)  # Eq. 25
    return (
        24
        * 60
        / math.pi
        * _GSC
        * dr
        * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))
    )  # Eq. 21


def et0_pm(
    doy: int,
    lat_deg: float,
    elev_m: float,
    tmax: float,
    tmin: float,
    tdew: float,
    rs_mj: float,
    u2: float,
) -> float:
    """FAO-56 Penman-Monteith reference ET0, mm/day (Eq. 6), G = 0."""
    tmean = (tmax + tmin) / 2
    p = 101.3 * ((293 - 0.0065 * elev_m) / 293) ** 5.26  # Eq. 7
    gamma = 0.000665 * p  # Eq. 8
    delta = 4098 * _es(tmean) / (tmean + 237.3) ** 2  # Eq. 13
    es = (_es(tmax) + _es(tmin)) / 2  # Eq. 12
    ea = _es(tdew)  # Eq. 14
    ra = _ra(doy, lat_deg)
    rso = (0.75 + 2e-5 * elev_m) * ra  # Eq. 37
    rns = 0.77 * rs_mj  # Eq. 38
    ratio = min(1.0, rs_mj / rso) if rso > 0 else 1.0
    rnl = (
        _SIGMA
        * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4)
        / 2
        * (0.34 - 0.14 * math.sqrt(ea))
        * (1.35 * ratio - 0.35)
    )  # Eq. 39
    rn = rns - rnl  # Eq. 40
    et0 = (0.408 * delta * rn + gamma * 900 / (tmean + 273) * u2 * (es - ea)) / (
        delta + gamma * (1 + 0.34 * u2)
    )  # Eq. 6
    return max(0.0, et0)


def weather_from_power(payload: dict) -> list[dict]:
    """NASA POWER daily point JSON (AG community) -> list of daily weather dicts; -999 -> None."""
    p = payload["properties"]["parameter"]
    names = {
        "tmax": "T2M_MAX",
        "tmin": "T2M_MIN",
        "tdew": "T2MDEW",
        "rs_mj": "ALLSKY_SFC_SW_DWN",
        "u2": "WS2M",
        "rain_mm": "PRECTOTCORR",
    }
    out = []
    for key in sorted(p["T2M_MAX"]):
        row = {"date": datetime.datetime.strptime(key, "%Y%m%d").date()}
        for k, name in names.items():
            v = p[name].get(key)
            row[k] = None if v is None or v == -999 else v
        out.append(row)
    return out


def _stage_kc(i: int, crop: dict) -> tuple[str, float]:
    """Stage name and single Kc for season day i (0-based); linear in development and late (Eq. 66).

    Kc_ini/mid/end are used as-is, without the FAO-56 climatic adjustment (Eq. 62, 65).
    """
    s, kc = crop["stages_days"], crop["kc"]
    a, b, c = (
        s["initial"],
        s["initial"] + s["development"],
        s["initial"] + s["development"] + s["mid"],
    )
    if i < a:
        return "initial", kc["ini"]
    if i < b:
        return "development", kc["ini"] + (i - a) / s["development"] * (kc["mid"] - kc["ini"])
    if i < c:
        return "mid", kc["mid"]
    return "late", kc["mid"] + min(1.0, (i - c) / s["late"]) * (kc["end"] - kc["mid"])


def _daily_et0(
    weather_by_date: dict, dates: list, lat_deg: float, elev_m: float
) -> tuple[list, list]:
    """ET0 and missing flags per date; missing ET0 inputs reuse the previous valid ET0."""
    et0, missing = [], []
    for d in dates:
        w = weather_by_date[d]
        missing.append(
            any(w.get(k) is None for k in ("tmax", "tmin", "tdew", "rs_mj", "u2", "rain_mm"))
        )
        ok = all(w.get(k) is not None for k in ("tmax", "tmin", "tdew", "rs_mj", "u2"))
        et0.append(
            et0_pm(
                d.timetuple().tm_yday,
                lat_deg,
                elev_m,
                w["tmax"],
                w["tmin"],
                w["tdew"],
                w["rs_mj"],
                w["u2"],
            )
            if ok
            else None
        )
    last = next((v for v in et0 if v is not None), 0.0)  # leading gap: use first valid value
    for i, v in enumerate(et0):
        if v is None:
            et0[i] = last
        else:
            last = v
    return et0, missing


def simulate_season(
    weather: list[dict],
    crop: dict,
    sow: datetime.date,
    lat_deg: float,
    elev_m: float,
    paddy: dict,
    soil: dict,
    initial_depletion_frac: float = 0.0,
    irrigation_cap_mm: float | None = None,
) -> dict:
    """Daily water balance of one crop season.

    upland: root-zone depletion bucket with Ks (FAO-56 Eq. 84-85); rain above field capacity is
    deep percolation; at the end of a day with Dr > RAW, irrigate back to Dr = 0 (within the cap).
    paddy: ponded layer h; day 0 land preparation fills the pond (not limited by the cap but counted
    in it); top up to target when h < target/2, runoff above max ponding.
    none (fallow): upland bucket without irrigation.
    """
    n = crop["duration_days"]["typical"]
    dates = [sow + datetime.timedelta(days=i) for i in range(n)]
    by_date = {w["date"]: w for w in weather}
    if any(d not in by_date for d in dates):
        raise ValueError("weather does not cover the season")
    et0s, missing = _daily_et0(by_date, dates, lat_deg, elev_m)

    regime = crop["water_regime"]
    stages = crop["stages_days"]
    grow = stages["initial"] + stages["development"]
    r = crop["root_depth_m"]
    p = crop["p_depletion"]
    cap = 0.0 if regime == "none" else irrigation_cap_mm  # None = unlimited
    target, hmax = paddy["target_ponding_mm"], paddy["max_ponding_mm"]
    thr = crop["heat"]["tmax_threshold_c"]

    def zr(i: int) -> float:
        return r["min"] + (r["max"] - r["min"]) * min(1.0, i / grow)

    def taw_at(i: int) -> float:
        return soil["taw_mm_per_m"] * zr(i)

    dr = initial_depletion_frac * taw_at(0)
    h = 0.0
    used = 0.0  # cumulative irrigation, mm
    tot = dict(et0=0.0, etc=0.0, rain=0.0, irr=0.0, out=0.0)
    stress = heat = 0
    daily = []
    for i, d in enumerate(dates):
        stage, kc = _stage_kc(i, crop)
        et0 = et0s[i]
        rain = by_date[d]["rain_mm"] or 0.0
        tmax = by_date[d]["tmax"]
        if stage == crop["heat"]["sensitive_stage"] and tmax is not None and tmax >= thr:
            heat += 1
        irr = out = 0.0
        ks = 1.0
        if regime == "paddy":
            etc = kc * et0
            if i == 0:
                irr, h = paddy["land_prep_mm"], target
                used += irr
            h += rain - etc - paddy["percolation_mm_day"]
            if h > hmax:
                out, h = h - hmax, hmax
            if h < 0.5 * target:
                add = target - h
                if cap is not None:
                    add = min(add, max(0.0, cap - used))
                irr += add
                used += add
                h += add
            if h < 0:
                stress += 1
                h = 0.0
            frac = min(1.0, h / target)
        else:
            taw = taw_at(i)
            raw = p * taw
            if dr > raw:
                ks = max(0.0, (taw - dr) / ((1 - p) * taw))
                stress += 1
            etc = ks * kc * et0
            dr = dr - rain + etc
            if dr < 0:
                out, dr = -dr, 0.0
            if dr > raw:
                irr = dr if cap is None else min(dr, max(0.0, cap - used))
                used += irr
                dr -= irr
            frac = max(0.0, min(1.0, 1 - dr / taw))
        for k, v in (("et0", et0), ("etc", etc), ("rain", rain), ("irr", irr), ("out", out)):
            tot[k] += v
        daily.append(
            {
                "date": d,
                "stage": stage,
                "kc": round(kc, 3),
                "et0": round(et0, 3),
                "etc": round(etc, 3),
                "rain": round(rain, 3),
                "irrigation": round(irr, 3),
                "water_frac": round(frac, 3),
                "ponding_mm": round(h, 3) if regime == "paddy" else None,
                "depletion_mm": round(dr, 3) if regime != "paddy" else None,
                "taw_mm": round(taw, 3) if regime != "paddy" else None,
                "root_depth_m": round(zr(i), 3),
                "ks": round(ks, 3),
            }
        )

    if regime == "paddy":
        depletion = 0.0 if h > 0 else 1.0
    else:
        depletion = dr / taw_at(n - 1)
    return {
        "sow": sow,
        "harvest": dates[-1],
        "et0_mm": round(tot["et0"], 1),
        "etc_mm": round(tot["etc"], 1),
        "rain_mm": round(tot["rain"], 1),
        "irrigation_mm": round(tot["irr"], 1),
        "runoff_or_deep_perc_mm": round(tot["out"], 1),
        "water_stress_days": stress,
        "heat_stress_days_sensitive": heat,
        "missing_days": sum(missing),
        "end_state": {"depletion_frac": round(depletion, 3)},
        "daily": daily,
    }
