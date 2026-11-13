# Provenance and Quality Contract

- Label value origin: `OBSERVED`, `ESTIMATED`, `ASSUMED`, `UNKNOWN`.
- Retain source URI, acquisition method, grid scale, coordinates, timestamp and version.
- Keep `FORECAST`, `CLIMATE_PROJECTION`, `CLIMATOLOGY`, `STRESS_TEST` distinct.
- Unknown essential features should trigger `UNKNOWN_REQUIRES_CHECK`; do not assume they are safe.
- Salinity: distinguish EC water (ECw) from root-zone ECe. A threshold for yield reduction is not automatically an exclusion rule.
- Soil SOC/NPK change may only be quantified with validated models/data; descriptive rotation benefits are conditional.
- Report missing source, stale data, fallback and confidence limits in DecisionPackage.
- Backtesting prohibits input data with `available_at > as_of`.
