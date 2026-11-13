# Data policy

- `catalog/sources.yaml`: registry of available *planned* adapters; all start as `connected: false`.
- `samples/`: tiny **synthetic** test/demo inputs only, not scientific validation data.
- Do not commit raw satellite imagery, raster/cubes, geocoded private farmer records or credentials.
- External datasets have separate licenses/terms; check rights and source attribution before distribution.
- Record spatial resolution, CRS, dates, issue/available time, quality flags, provenance and unit conversion.
- Store actual data in a controlled object store/cache and metadata in persistence layer when implemented.

See [Provenance and Quality](../docs/data/PROVENANCE_AND_QUALITY.md).
