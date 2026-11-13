# Data Sources

This page documents intended connections, **not currently integrated products**. See `data/catalog/sources.yaml` and the source table in [Solution Design](../architecture/SOLUTION_DESIGN.md).

NASA: POWER historical climate; GPM IMERG precipitation; SMAP L4 regional moisture; Landsat/HLS plant phenology; NASADEM elevation; POWER Projection API future climate scenarios. Seasonal forecasting (GEOS-S2S/Copernicus) needs access/skill confirmation; salinity/hydrology needs local feeds. Non-NASA: SoilGrids, FAO parameters, local agronomic reports, field measurements and farmer constraints.

On each ingestion: persist product/version, units, CRS/grid footprint, timestamps (`observed_at`, `available_at`, `issue_time`), validity/quality, URL/license and caveats. Unit and source decisions must be peer-reviewed.
