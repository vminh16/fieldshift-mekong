# FieldShift-Mekong: overnight data handoff

Start with [data_inventory.json](data_inventory.json). It lists every named source plus extras (33 entries), actual files/row counts/date ranges, coverage evidence, and live job PIDs/logs/resume commands. A detached watcher refreshes it every 30 seconds while jobs remain. An entry marked `SCRIPT_READY_NEEDS_TIME` is incomplete even if a partial processed file exists.

## Read the data

Processed point data are in `apps/api/src/fieldshift/resources/observations/<source>/<site>.json.gz`. Every bundle has source/product/version, units and applied scale, spatial resolution, cell center (or explicitly unknown), dates, retrieval time, QA notes and licence, then `series`. Each gzip is below 2 MB. Site names are `cantho`, `chaudoc`, `bentre`, `soctrang`.

```python
import gzip
import json
from pathlib import Path

root = Path('apps/api/src/fieldshift/resources/observations')
with gzip.open(root / 'imerg_monthly' / 'cantho.json.gz', 'rt') as f:
    data = json.load(f)
print(data['variables'], data['time_range'], data['qa_note'])
rows = data['series']
```

`imerg_monthly` contains 297 complete months/site, **2001-01 through 2025-09**. Values are monthly totals, converted from the NASA DAS rate `mm/hr × 24 × calendar_days`. Row dates label the first day of the month. `imerg_late` contains daily `mm/day` values unchanged from the source; it is downloading 2023-01-01 through the latest CMR day. Read `progress.json` under the corresponding raw cache directory to distinguish partial from complete runs. Do not add a second factor of 24.

`era5_openmeteo` has **9,443 daily rows/site, 2001-01-01 through 2026-11-08**, four variables: Tmax/Tmin, precipitation and reference ET0. Explicit `models=era5`, UTC, nearest grid and disabled elevation adjustment keep it reproducible. Recent ERA5T is preliminary. Comparisons with POWER are inside each header; ET0 is compared with the project's FAO-56 calculation using POWER meteorology and bundled SRTM elevation, excluding missing inputs.

`gldas` is the working **monthly** GLDAS Noah 2.1 fallback. Data Rods has been discontinued, and AppEEARS does not list GLDAS. It uses cloud OPeNDAP for SoilMoi0_10cm/10_40cm, Evap and Rainf. Raw soil water is kg/m²; volumetric fractions divide by 100 and 300 respectively. Monthly flux totals multiply kg/m²/s by seconds in the month. Historical availability ends July 2026. This dataset cannot describe today's moisture.

`gaez` has **41 static layers/site**: all-land rainfed suitability and current-cropland irrigated suitability for wetland rice, maize, soybean and groundnut, high/low management and water-supply variants, plus soil constraints. Preserve the row's crop, water supply, management and layer ID when using a value. Suitability is retained as an index **0–10000**; display percent is index/100. Soil constraints retain their source class/rating. There is **no mungbean layer**: do not substitute another legume. Dates label historical/static baselines, not acquisition dates. `selected_layers.json` in the raw cache gives complete FAO metadata and download URLs.

`power` and `srtm` repackage the existing verified integrations. SRTM's row date labels the February 2000 mission, not an independently known pixel acquisition date. Cell centers left `null` are explicitly unverified; requested coordinates are not passed off as pixel centers.

AppEEARS datasets will appear as `smap`, `modis_vi`, `modis_et`, `ecostress_lst`, `ecostress_et`, `hls_l30`, `hls_s30` and HLS QA companions when their tasks finish. Their processor is **[UNVERIFIED end-to-end until a real bundle completes]**. Point CSV values are already scaled by AppEEARS: local multiplier is 1. QA is retained; counts of present values do not prove cloud-clear observations. Join HLS VI to its acquisition's Fmask before interpreting it. Never convert MOD16 composite ET into daily ET0 without checking the composite length. Both existing task IDs are fixed in the inventory; resumption cannot create a replacement task.

## Projection scenarios already used by the engine

`resources/projections/{cantho,chaudoc,bentre,soctrang}.json` each contains **8 series × 312 months = 2,496 monthly values**, 2025–2050: ACCESS-CM2 and MPI-ESM1-2-HR, SSP245/585, tasmax/pr. The engine can now load four climate projection scenarios for every demo site. Independent verification recalculates every monthly value from daily CSVs, checks leap years and units. These are climate scenarios with no assigned probability.

The new observation files are packaged resources ready for readers; their acquisition does not automatically change the planner's existing data-source selection or QA policy.

## Cross-check against POWER

All 297 matched months, bias = IMERG minus POWER, units mm/month:

| Site | Pearson r | Mean bias |
|---|---:|---:|
| cantho | 0.833856 | +24.99514 |
| chaudoc | 0.702449 | +36.99216 |
| bentre | 0.886910 | +4.83204 |
| soctrang | 0.917303 | +8.36970 |

These compare two regional estimates. They are not validation against local rain gauges. ERA5 daily comparisons for all four variables are in its headers. No bias correction was applied.

## Operational checks

From the repository root:

```sh
. .venv/bin/activate
python scripts/data/update_inventory.py
python scripts/data/verify_observations.py
python scripts/data/verify_data_access.py
make test
python -m ruff check apps/api scripts
python -m ruff format --check apps/api scripts
```

Logs are under `.fieldshift/logs/`; raw response windows/CSVs/catalogs are under `.fieldshift/cache/<source>/`. Successful raw chunks are reused on resume. Downloads use IPv4. Earthdata credentials remain in `~/.netrc`; bearer tokens stay in process memory; curl's private cookie file is removed at normal exit. No credentials are in the inventory, commands, processed resources or logs.

The watcher retries failed jobs at most three times, always resuming the **same** AppEEARS task ID. It stops when all jobs complete or after 24 hours. `jobs[].running`, `complete`, `restart_count`, `pid`, `log` and `resume` are available in the inventory. Resume the watcher with the recorded command if necessary. Do not run a second poller while the recorded process is alive.

## Important gaps and corrected coverage claims

- **SoilGrids:** its existing four cache files contain only null values: zero usable measurements. `FETCHED` records the cache artifact; runtime regional soil fallback remains an assumption. GAEZ adds independent static constraints.
- **GEDI:** CMR L4A V3 granules intersect the four ±0.005° windows (23/24/14/17). This is granule-level evidence only; exact laser footprint intersection is **[UNVERIFIED]**. Woody biomass is not a useful rice-field state variable.
- **US regional products:** WSS, CDL, PRISM, SSURGO/STATSGO2, NAIP, NLCD, NLDAS, CoCoRaHS, NWIS, NASS QuickStats, OpenET and LANDFIRE exclude Vietnam for the intended local data use. Official evidence and our substitutes are recorded individually. CoCoRaHS/NLDAS include some countries beyond the US; OpenET now covers all 48 contiguous states, not just the west.
- **AMS and Ag Data Commons:** a blanket “US-only” claim is unsupported. AMS also has international reporting; Ag Data Commons is a research repository scoped by funding, not geography. Both are `NOT_USEFUL_HERE` because no appropriate local data series was established.
- **Worldview:** [12 PNGs and manifest](images/README.md), 4.36 MB. Aligned 16-day NDVI composite dates differ from true-color dates. Images are browse illustrations; transparent rain imagery is ambiguous.
- **Salinity:** none of these measurements provide canal ECw. Use farmer/site measurements, with explicit uncertainty otherwise.

No git commit, push or stash was performed.
