import datetime
import gzip
import json
import math
from pathlib import Path

from fieldshift.infrastructure.crop_models.fao56_water import (
    et0_pm,
    simulate_season,
    weather_from_power,
)

CANTHO = (
    Path(__file__).resolve().parents[2] / "src/fieldshift/resources/demo_cache/power/cantho.json.gz"
)
PADDY = {
    "percolation_mm_day": 3,
    "land_prep_mm": 150,
    "target_ponding_mm": 50,
    "max_ponding_mm": 100,
}
SOIL = {"taw_mm_per_m": 150}
RICE = {
    "duration_days": {"typical": 105},
    "stages_days": {"initial": 20, "development": 30, "mid": 35, "late": 20},
    "kc": {"ini": 1.05, "mid": 1.20, "end": 0.90},
    "root_depth_m": {"min": 0.3, "max": 0.5},
    "p_depletion": 0.2,
    "water_regime": "paddy",
    "heat": {"sensitive_stage": "mid", "tmax_threshold_c": 35},
}
MUNG = {
    "duration_days": {"typical": 75},
    "stages_days": {"initial": 15, "development": 25, "mid": 25, "late": 10},
    "kc": {"ini": 0.4, "mid": 1.05, "end": 0.6},
    "root_depth_m": {"min": 0.3, "max": 0.8},
    "p_depletion": 0.45,
    "water_regime": "upland",
    "heat": {"sensitive_stage": "mid", "tmax_threshold_c": 35},
}


def test_fao56_example18():
    x = math.log(1.409 / 0.6108)
    tdew = 237.3 * x / (17.27 - x)
    doy = datetime.date(2001, 7, 6).timetuple().tm_yday  # 187
    et0 = et0_pm(doy, 50 + 48 / 60, 100, 21.5, 12.3, tdew, 22.07, 2.078)
    print("ET0 example 18:", et0)
    assert abs(et0 - 3.9) < 0.15


def test_real_data():
    w = weather_from_power(json.loads(gzip.decompress(CANTHO.read_bytes())))
    rice = simulate_season(w, RICE, datetime.date(2015, 12, 1), 10.03, 1.91, PADDY, SOIL)
    mung = simulate_season(w, MUNG, datetime.date(2016, 3, 1), 10.03, 1.91, PADDY, SOIL)
    for r in (rice, mung):
        print({k: v for k, v in r.items() if k != "daily"})
        assert r["et0_mm"] > 0 and r["etc_mm"] > 0 and r["irrigation_mm"] > 0
    assert rice["irrigation_mm"] > mung["irrigation_mm"]
    # upland mass balance: rain + irrigation - etc - drainage = change in storage (storage = -Dr, Dr0 = 0)
    taw_end = SOIL["taw_mm_per_m"] * MUNG["root_depth_m"]["max"]
    d_storage = -mung["end_state"]["depletion_frac"] * taw_end
    bal = mung["rain_mm"] + mung["irrigation_mm"] - mung["etc_mm"] - mung["runoff_or_deep_perc_mm"]
    assert abs(bal - d_storage) < 1.0
    dry = simulate_season(
        w, MUNG, datetime.date(2016, 3, 1), 10.03, 1.91, PADDY, SOIL, irrigation_cap_mm=0
    )
    assert dry["water_stress_days"] > mung["water_stress_days"]
    assert dry["irrigation_mm"] == 0
