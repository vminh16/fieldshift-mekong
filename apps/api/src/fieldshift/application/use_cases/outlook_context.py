"""Wire optional outlook and regional hydrology adapters into the historical context."""

from fieldshift.infrastructure.data_sources.forecasts.open_meteo_seasonal import load_seasonal
from fieldshift.infrastructure.data_sources.glofas import load_discharge
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
    ctx.update(
        forecast=forecast,
        projections=projections,
        outlook_notes=notes,
        upstream_discharge=discharge,
    )
    ctx["sources_status"].update(
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
