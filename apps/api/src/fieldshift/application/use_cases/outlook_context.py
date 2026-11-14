"""Wire optional outlook and regional hydrology adapters into the historical context."""

from fieldshift.infrastructure.data_sources import enso
from fieldshift.infrastructure.data_sources.forecasts.open_meteo_seasonal import load_seasonal
from fieldshift.infrastructure.data_sources.glofas import load_discharge
from fieldshift.infrastructure.data_sources.nasa import imerg
from fieldshift.infrastructure.data_sources.nasa.nex_cmip6 import RELEASE_DATE, load_projections

OPEN_METEO = {
    "attribution": "Weather data by Open-Meteo.com / ECMWF (non-NASA)",
    "attribution_url": "https://open-meteo.com/",
    "license": "CC-BY 4.0",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "spatial_scale": "regional",
}


def add_outlook(ctx, field, as_of):
    ck = field["profile"].get("cache_key")
    forecast, forecast_status = load_seasonal(field["lat"], field["lon"], as_of, ck)
    projections, notes = load_projections(ck, as_of)
    discharge, discharge_status = load_discharge(as_of)
    latest = enso.latest_oni(as_of)
    monthly = imerg.load_imerg_monthly(ck)
    # AC-04: drop IMERG months not fully before as_of (the bundle may extend past a hindcast).
    monthly = monthly and {k: v for k, v in monthly.items() if k < (as_of.year, as_of.month)}
    ctx.update(
        enso={
            "oni": enso.load_oni(),
            "latest": latest,
            "source": enso.SOURCE,
            "imerg_source": imerg.SOURCE,
        },
        imerg_monthly=monthly or None,
        forecast=forecast,
        projections=projections,
        outlook_notes=notes,
        upstream_discharge=discharge,
    )
    ctx["sources_status"].update(
        NOAA_ONI="BUNDLED" if latest else "ONI_NOT_AVAILABLE_AT_AS_OF",
        IMERG_MONTHLY="BUNDLED" if monthly else "NOT_BUNDLED_FOR_SITE_POWER_FALLBACK",
        OPEN_METEO_SEASONAL=forecast_status,
        GLOFAS=discharge_status,
        NEX_GDDP_CMIP6=(
            "CACHED"
            if projections
            else "PROJECTION_UNAVAILABLE_AT_AS_OF"
            if as_of < RELEASE_DATE
            else "INSUFFICIENT_COVERAGE"
        ),
    )
    ctx["evidence"].update(
        {
            "ev_enso_oni": {
                "kind": "OBSERVED_INDEX",
                "source": enso.SOURCE + " (non-NASA)",
                "url": enso.SOURCE_URL,
                "retrieved": enso.RETRIEVED,
                "license": enso.LICENCE,
                "spatial_scale": "ocean basin (Niño-3.4)",
                "status": ctx["sources_status"]["NOAA_ONI"],
                "time_scope": [None, f"{latest[0]}-{latest[1]:02d}"] if latest else None,
                "limitations": [
                    "ONI là chỉ số của NOAA (không phải NASA), đo nhiệt độ mặt biển Thái Bình Dương, không phải mưa tại ruộng.",
                    "Chỉ dùng tháng có cửa sổ 3 tháng đã kết thúc trước tháng của as_of (không nhìn trước, AC-04); NOAA có thể hiệu chỉnh lại giá trị cũ.",
                    "Năm tương tự là liên hệ thống kê với ~24 năm dữ liệu, KHÔNG phải dự báo mưa hay mặn; có năm El Niño vẫn mưa nhiều.",
                    "ENSO riêng lẻ không dời khung mặn; kế hoạch 2026–27 có thể dùng giả định sớm hơn nếu có dẫn bản tin SIWRR.",
                ],
            },
            "ev_imerg_monthly": {
                "kind": "OBSERVED_REMOTE_ESTIMATE",
                "source": imerg.SOURCE + " (GPM_3IMERGM)",
                "url": "https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary",
                "spatial_scale": "regional",
                "resolution": "0.1 deg (~11 km)",
                "status": ctx["sources_status"]["IMERG_MONTHLY"],
                "time_scope": [
                    "{}-{:02d}".format(*min(monthly)),
                    "{}-{:02d}".format(*max(monthly)),
                ]
                if monthly
                else None,
                "limitations": [
                    "Ước tính vệ tinh ô lưới ~11 km, chưa hiệu chỉnh với trạm đo tại chỗ.",
                    "Chỉ dùng mùa khô (tháng 12–4) đã kết thúc trước as_of; không có cho thửa ngoài 4 điểm demo (khi đó dùng NASA POWER).",
                    "Mô phỏng nước của năm tương tự vẫn chạy trên ngày NASA POWER cùng năm; IMERG chỉ dùng cho thống kê mưa mùa khô.",
                ],
            },
            "ev_seasonal_forecast": {
                **OPEN_METEO,
                "kind": "FORECAST",
                "source": "Open-Meteo Seasonal / ECMWF SEAS5 (non-NASA)",
                "url": "https://open-meteo.com/en/docs/seasonal-forecast-api",
                "issue_time": forecast["issue_time"] if forecast else None,
                "available_at": forecast["available_at"] if forecast else None,
                "status": forecast_status,
                "resolution": "36 km",
                "quality_flags": forecast["quality_flags"]
                if forecast
                else ["FORECAST_UNAVAILABLE"],
                "limitations": [
                    "Skill not evaluated for Mekong; no calibrated probabilities.",
                    "Not bias corrected; regional estimate, not field observation.",
                    "Members with incomplete/invalid windows (including negative precipitation in the API) omitted, never filled with zero.",
                    "Temperature/precipitation members spliced onto POWER analog years after ~180 days; dew point, radiation and wind always from analog days.",
                ],
            },
            "ev_nex_cmip6": {
                "kind": "PROJECTION",
                "source": "NASA NEX-GDDP-CMIP6 v2.0 via NCCS NCSS",
                "version": "2.0",
                "url": "https://nccs.smce.nasa.gov/data-collections/nex-gddp-cmip6/",
                "spatial_scale": "regional",
                "resolution": "0.25 deg",
                "status": ctx["sources_status"]["NEX_GDDP_CMIP6"],
                "limitations": [
                    "2041–2050 minus 2025–2034 monthly Tmax delta and precipitation ratio applied to POWER analog days.",
                    "Only Tmax and precipitation adjusted; Tmin, dew point, radiation and wind unchanged.",
                    "SSPs have no assigned probability; not weather forecasts.",
                    *notes,
                ],
            },
            "ev_glofas": {
                **OPEN_METEO,
                "kind": "MODEL_ESTIMATE",
                "source": "Open-Meteo Flood / Copernicus GloFAS (non-NASA)",
                "url": "https://open-meteo.com/en/docs/flood-api",
                "resolution": "5 km",
                "status": discharge_status,
                "location": {"name": "Mekong at Tân Châu", "lat": 10.80, "lon": 105.24},
                "limitations": [
                    "Modeled regional river discharge, not salinity or canal ECw; river cell requires local verification.",
                    "Trailing 7-day mean vs same calendar window in available 2001–2020 years; anomaly is not a calibrated salinity threshold.",
                    "Recent discharge may be modeled forecast data; only days through retrieval/as_of used.",
                ],
            },
        }
    )
    return ctx
