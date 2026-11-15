# FieldShift Mekong

**Climate-adaptive crop rotation planning from NASA data, one field at a time.**
NASA Space Apps Challenge 2026 · [Field Shift: Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/)

- **Live app:** https://fieldshift.loanhviet.dev
- **Demo video (30 s):** https://youtu.be/ZiyXVJEjSy8

## Try it in one minute

1. Open https://fieldshift.loanhviet.dev and click **Ruộng của tôi** (My fields).
2. Pick **Ruộng mẫu Sóc Trăng** (sample field, coastal Sóc Trăng) and open **Đề xuất luân canh** (Rotation advice).
3. Read the answer: rest the saltiest season and keep the main winter–spring rice crop. Crops stand in the regional salinity window for **84 days instead of 177**, and the plan beats current practice in **12 of 12** weather scenarios.

The model covers the **Mekong Delta only** (8–11.5° N, 104–107.5° E). Four sample fields ship with cached NASA data and give different answers:

| Sample field | Setting | Top strategy | Days in salinity window (plan / current) | Scenarios won · confidence |
|---|---|---|---|---|
| Sóc Trăng | coastal | rice – fallow/cover crop – rice | 84 / 177 | 12/12 · medium |
| Bến Tre | coastal | rice – fallow/cover crop – rice | 84 / 177 | 12/12 · medium |
| Cần Thơ | inland | rice – peanut – rice | 161 / 177 | 4/12 · low |
| Châu Đốc | upstream | rice – peanut – rice | 177 / 177 | 1/12 · low |

Inland and upstream the engine reports low confidence because no alternative clearly beats current practice there. Sample fields cannot be deleted or moved; draw your own parcel to experiment (the first plan for a new field takes about 20 s while NASA data is fetched).

## What it does

FieldShift answers one question for one field: *which crop sequence should we plant over the next three seasons, and how sure can we be?* The intended user is a commune extension officer or cooperative advising farmers.

1. **Locate the field** on a 3D globe and satellite imagery; draw it, drop a pin or use GPS.
2. **Year outlook.** NOAA ONI picks past years with a similar ENSO state; NASA GPM IMERG shows how much dry-season rain fell in those years (2026–27: strong El Niño, about 30% of normal). Shown as a statistical signal, never as a forecast.
3. **Rotation engine.** Generates every rotation that fits the regional calendar (rice, maize, soybean, mungbean, peanut, sesame, watermelon, fallow/cover crop), simulates each day by day with a FAO-56 water balance driven by NASA POWER, applies heat, waterlogging and salinity-overlap rules, and keeps the Pareto-optimal options across 12 scenarios.
4. **Decision package.** Current practice next to 2–5 conditional strategies, each with scenarios won, a confidence level, the reason, a pre-sowing checklist and field triggers (for example: measure canal water salinity; above 2 dS/m, re-plan).
5. **Simulation and season tracking.** Replay two rotations week by week; log field measurements during the season and get flagged when a trigger fires.

## NASA data and what each source does

| Source | Role in the result |
|---|---|
| NASA POWER Daily (MERRA-2/CERES) | Daily weather → reference evapotranspiration → FAO-56 water balance, irrigation and stress days |
| NASA POWER GWETROOT | Initial root-zone soil moisture |
| NASA GPM IMERG V07 Final Monthly | Dry-season rain in ENSO analog years (year outlook) |
| NASA NEX-GDDP-CMIP6 | Four 2041–2050 climate futures used to test robustness |
| SRTM | Elevation term in evapotranspiration |
| NASA Blue Marble | Globe texture |

Non-NASA sources (NOAA ONI, ERA5, ECMWF SEAS5, GloFAS, ISRIC SoilGrids, FAO-56, the 2026 Vietnamese crop-calendar guidance) are listed with their role and limits in the app's **Dữ liệu NASA** tab and in [docs/data/SOURCES.md](docs/data/SOURCES.md).

## Evidence and limits

- No look-ahead: plans only use data published before the planning date.
- Backtests on 2016 and 2020 weather: [docs/BACKTEST_REPORT.md](docs/BACKTEST_REPORT.md). ENSO hindcast with the right wet/dry direction in 12 of 15 cases: [docs/YEAR_OUTLOOK_REPORT.md](docs/YEAR_OUTLOOK_REPORT.md).
- Rules with sources and evidence grades: [docs/RULES.md](docs/RULES.md). Sensitivity analysis: [docs/SENSITIVITY_REPORT.md](docs/SENSITIVITY_REPORT.md).
- Known limits: [docs/LIMITATIONS.md](docs/LIMITATIONS.md). Grid cells (about 50 km) are not field measurements, field salinity is not predicted, and value weights are a team heuristic, not a yield or profit model. **Not for real farming decisions without local verification.**

## Run it locally

Requirements: Docker, or Python 3.11+ and Node.js 22+. No NASA credentials are needed; the sample fields run offline.

**Docker (same stack as production):**

```bash
docker compose -f infra/compose.oracle.yaml up --build
# app: http://localhost:18101   API health: http://localhost:18100/v1/health
```

**Development:**

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e './apps/api[dev]'
make api-dev                      # API on http://localhost:8000 (docs at /docs)

cd frontend && npm ci && npm run dev   # web on http://localhost:5180
```

Plan a sample field from the command line:

```bash
curl -X POST localhost:8000/v1/plans -H 'Content-Type: application/json' -d '{"field_id":"fld_soctrang"}'
```

Runtime data (SQLite and the NASA cache for new fields) goes to `FIELDSHIFT_DATA_DIR` (default `.fieldshift/`).

```bash
make test     # backend tests, offline
make lint     # ruff
```

## Repository layout

```text
apps/api/        FastAPI backend: API → application use cases → domain engines ← infrastructure adapters
frontend/        React 19 + TypeScript + Vite web app (MapLibre, three.js)
contracts/       Shared types and captured engine responses
docs/            Product, architecture, data, reports and the Space Apps submission
infra/           Docker Compose files and the VM deploy script
scripts/         Data fetching, backtests, sensitivity analysis, demo video pipeline
```

More detail: [Solution design](docs/architecture/SOLUTION_DESIGN.md) · [Backend, API and DB](docs/architecture/BACKEND_API_DB.md) · [Problem statement](docs/product/PROBLEM_STATEMENT.md) · [Deployment](docs/operations/DEPLOYMENT.md).

## Deployment

`main` deploys automatically to https://fieldshift.loanhviet.dev after CI passes (`.github/workflows/deploy.yml`). The workflow ships the commit to the VM, where `infra/oracle/deploy.sh` builds the new release next to the running one, swaps, health-checks and rolls back on failure.

## AI usage

AI tools (Claude Code, OpenAI Codex) helped write code, review and research; the demo voice-over is AI-generated. The engine itself uses no AI model. Details: [docs/AI_USAGE.md](docs/AI_USAGE.md).

## License

[MIT](LICENSE)
