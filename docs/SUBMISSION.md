# NASA Space Apps 2026: submission form content

Challenge: **Field Shift: Adapting Farms with NASA Data**. Fields below follow the order of the official form, ready to paste.

> Before submitting:
> 1. Make the GitHub repository public. It is private now, and the form requires links that open without permission or login.
> 2. Upload the 30 s video (YouTube "Unlisted" or "Public", or Google Drive "Anyone with the link") and paste the full URL.
> 3. Have the team check the TODO in `docs/AI_USAGE.md`.
> 4. Choose a LICENSE.

---

## Project Name

**FieldShift Mekong: climate-adaptive crop rotation from NASA data, one field at a time**

## Summary (≈190 words, paste as is)

FieldShift Mekong is a decision-support web app that helps Mekong Delta farmers and extension officers choose crop rotations for the next three seasons as salinity and drought intensify. A farmer draws their parcel on satellite imagery. FieldShift then simulates every feasible rotation day by day, using a FAO-56 soil-water balance driven by NASA POWER weather and initialised with POWER root-zone wetness. Each rotation is compared against the farmer's current sequence across 12 scenarios: climatology, dry, hot and early-salinity stress tests, an ENSO analog year built from NOAA ONI and NASA GPM IMERG rainfall, a seasonal forecast, and four NASA NEX-GDDP-CMIP6 climate futures out to 2050.

For a coastal Sóc Trăng field facing the strong 2026–27 El Niño, the top strategy keeps the main winter–spring rice crop, sows it early and rests the saltiest season. This cuts the days crops stand in the salinity window from 177 to 84, and the strategy holds in 12 of 12 scenarios.

Every number shows its source, its uncertainty and what must be checked in the field first, such as canal water salinity. A weekly digital twin with 3D soil blocks then lets farmers see why one rotation is safer.

## Project Demonstration

`<paste the full public URL of the 30 s video (YouTube / Google Drive)>`

The file is `FieldShift_demo_30s.mp4`, 29.9 s, 1080p. Vietnamese subtitles are burned in and the voice-over is in English.

## Project

`https://github.com/vminh16/fieldshift-mekong` (make it public first)

---

## Project Details

### What it does

FieldShift answers one question for one field: **"Which crop sequence should I plant over the next three seasons, and how sure can I be?"** The flow has six steps.

1. **Locate and draw.** The farmer searches for a place on a 3D globe and flies down to satellite imagery, then draws the parcel by clicking its corners. GPS and walk-the-boundary are also available.
2. **Field profile.** The current rotation, irrigation and drainage are recorded. Anything the farmer has not told us is stored as an *assumption*, never as a farmer-reported fact.
3. **Year outlook.** The app asks "What will next dry season look like?". It takes the latest NOAA ONI value published *before* the planning date and picks analog years. For 2026–27 the ONI is +2.5 (strong El Niño), and the analog years are 2015–16 and 2023–24. NASA GPM IMERG then shows that dry-season rain in those years was about 30 % of normal (49 mm vs 161 mm).
4. **Rotation engine.** The engine generates every rotation that fits the regional crop calendar: rice, maize, soybean, mungbean, peanut, sesame, watermelon or a fallow/cover crop, with early or standard sowing. It simulates each one day by day with a FAO-56 dual water balance (ET₀ from NASA POWER, Kc curves, paddy ponding, drainage), adds heat, waterlogging and salinity-overlap rules, and keeps the Pareto-optimal options on irrigation need, stress days, salinity exposure and a season-value index. It does this across 12 scenarios. Up to three seasons it searches exhaustively; longer horizons use beam search.
5. **Decision package.** The result has 2–5 conditional strategies (water-saving, low-risk, early-sow salinity avoidance, regional practice) next to the current sequence. Each comes with a robustness score (wins out of 12 scenarios), a confidence level, a plain-language reason, a pre-sowing checklist and field triggers, for example "measure canal ECw; if it exceeds the threshold, re-plan".
6. **Digital twin and tracking.** Two chains can be replayed week by week on a shared calendar, with a chart of cumulative irrigation, the salinity window and stress weeks, plus two 3D cut-away soil blocks showing canal, ponded water, roots and soil moisture. "What-if" lets users change sowing dates or water caps. During the season, farmers log measurements, and the plan is flagged "needs re-planning" when a trigger fires.

### Why it matters (intended impact)

- The Mekong Delta produces about half of Vietnam's rice. Saline intrusion and El Niño droughts (2015–16, 2019–20) caused large losses, and official guidance for 2026–27 (Công văn 2504/TTTV-TTBVTV, 19 June 2026) already calls for adjusting seasons and switching to upland crops.
- Farmers get this guidance as province-wide bulletins. FieldShift turns it into a **field-specific, comparable and checkable** plan, showing what to change, by how much, under which conditions, and what to measure first.
- It is built for low-literacy, low-bandwidth use: Vietnamese UI, one answer first, photos of crops on a month timeline, a phone-friendly layout, and a printable summary for extension officers.

### Scientific honesty (what makes it trustworthy)

- **No look-ahead.** Every input is restricted to data available before the planning date. CMIP6 is blocked for planning dates before its 2022 release.
- **Scenario kinds are never mixed.** Climatology, forecast, climate projection and stress test are labelled separately, and only climatology and dry-year criteria pick the shortlist. Forecasts and projections test robustness and confidence.
- **Source conflicts are explicit.** NASA POWER Tmax runs +2.8 to +4.1 °C warmer than ERA5 inland in March. We correct it monthly *for heat-day counting only* and keep the original POWER data for ET₀. This is documented in `docs/HEAT_BIAS_REPORT.md`.
- **Evidence in the repo:** 13 rules with sources and an A/B/C classification (`docs/RULES.md`), a sensitivity analysis (`docs/SENSITIVITY_REPORT.md`), backtests on 2016 and 2020 weather, an ENSO hindcast with the right wet/dry direction in 12 of 15 cases (`docs/YEAR_OUTLOOK_REPORT.md`), and a full limitations page (`docs/LIMITATIONS.md`).
- **Known limits are stated in the app.** Grid cells (about 50 km) are not field measurements. Soil data is missing at the demo sites. Salinity dates are assumptions until canal ECw is measured. The value weights are a team heuristic, not a yield or profit model.

### How we used NASA data

| NASA resource | Role in FieldShift |
|---|---|
| NASA POWER Daily API (MERRA-2/CERES) | **Decision.** Daily Tmax/Tmin/dew point/wind/solar/rain drive FAO-56 ET₀ and the water balance for every scenario |
| NASA POWER GWETROOT | **Decision.** Initial root-zone soil-water state |
| GPM IMERG V07 Final monthly | **Evidence.** Dry-season rainfall of ENSO analog years and the ONI–rain correlation (r = −0.41 to −0.71) |
| NEX-GDDP-CMIP6 v2.0 (ACCESS-CM2, MPI-ESM1-2-HR; SSP2-4.5 and SSP5-8.5; 2041–2050) | **Robustness.** Four climate-future scenarios. A strategy that loses in them is flagged and cannot be rated HIGH confidence |
| SRTM 30 m | **Context.** Elevation in the ET₀ pressure term; terrain context |
| NASA Blue Marble | Earth texture of the landing globe |

SMAP, MODIS, Landsat/HLS, ECOSTRESS and GRACE are listed in the app as **not yet used**. They are the next step: SMAP for initial soil moisture and HLS/MODIS NDVI to detect the current rotation.

### Tools and technologies

- **Backend:** Python 3.11, FastAPI, SQLite, httpx, pytest (104 tests), ruff, OpenAPI contract with generated TypeScript types.
- **Frontend:** React 19, TypeScript, Vite, MapLibre GL JS (satellite map and parcel drawing), three.js (3D globe and 3D soil blocks), Be Vietnam Pro font.
- **Data scripts:** Python fetchers and verification for POWER, IMERG, GLDAS, ERA5, GAEZ, CMIP6 and NOAA ONI, with a data inventory (`docs/data/`).
- **CI:** GitHub Actions for tests, lint, contract check and the frontend build.
- **Demo video:** Playwright + Chrome screen capture of the real app, ffmpeg, HTML/CSS overlays, Chatterbox TTS (AI voice) and procedurally synthesized music.

### What makes it creative

- **An ENSO analog-year outlook.** It answers "Which past year will next dry season look like?" with NASA rainfall evidence, without pretending to be a forecast.
- **Rotation planning as a multi-scenario Pareto search**, instead of a single "best crop". It always shows the current practice side by side.
- **A digital twin that only replays engine results.** It is never a separate model, so what you see is exactly what was computed.
- **"Days crops stand in salt"** as a farmer-readable metric, connected to field triggers that turn the plan into a living, re-plannable document.

### Factors the team considered

Farmers' first question is "Do I keep my main rice crop?", so the engine protects the winter–spring rice season through a season-value heuristic. We also considered:

- the official 2026 guidance and regional sowing calendars;
- missing data (soil, canal salinity), which is shown as *unknown* plus a checklist and never invented;
- the uncertainty of ENSO signals, so we deliberately softened the claims;
- grid-to-field mismatch, offline demo caches and phone screens;
- not overclaiming: the app states that its outputs are model estimates that must be verified in the field.

---

## Use of Super Intelligence (SI)

**Options to tick:**
- ☑ Data Analysis and Interpretation
- ☑ Presentation, Video, or Audio
- ☑ Coding, Debugging, or Troubleshooting

Also tick Research or Writing if the form offers it, because the documentation and the product audit were AI-assisted.

**What judges can see (already in the project):**
- **Code and data.** `docs/AI_USAGE.md` declares Claude Code (Anthropic: Claude Opus 5.5, Sonnet 5.5, Fable 5.2) for code generation, review, product audit and research, and OpenAI Codex for implementation tasks. All AI output was reviewed with automated tests, type checks, backtests and the documented limitations. The team made the scope and agronomic decisions.
- **Video.** The images are real screen recordings of the app, not generated images. The **voice-over is AI-generated** with Chatterbox TTS (Resemble AI, MIT), using a male voice cloned from a Kokoro-82M (Apache-2.0) reference. The music is synthesized in code. This is stated on the video's end card and in the MP4 metadata (`comment` tag).
- **No NASA logos or branding** were generated or modified. "NASA" appears only as text naming the data sources.

---

## NASA Data (Link Text → Link URL)

| Link Text | Link URL |
|---|---|
| NASA POWER Daily API (MERRA-2/CERES) | https://power.larc.nasa.gov/ |
| NASA POWER API documentation (daily point) | https://power.larc.nasa.gov/docs/services/api/temporal/daily/ |
| GPM IMERG V07 Final Monthly (GPM_3IMERGM) | https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary |
| NASA NEX-GDDP-CMIP6 | https://www.nccs.nasa.gov/services/data-collections/land-based-products/nex-gddp-cmip6 |
| SRTM (Shuttle Radar Topography Mission) | https://www.earthdata.nasa.gov/data/instruments/srtm |
| NASA Blue Marble (Earth texture) | https://visibleearth.nasa.gov/collection/1484/blue-marble |

## Space Agency Partner & Other Data

| Link Text | Link URL |
|---|---|
| ERA5 reanalysis via Open-Meteo (ECMWF/Copernicus) | https://open-meteo.com/en/docs/historical-weather-api |
| ECMWF SEAS5 seasonal forecast via Open-Meteo | https://open-meteo.com/en/docs/seasonal-forecast-api |
| GloFAS river discharge via Open-Meteo | https://open-meteo.com/en/docs/flood-api |
| NOAA PSL Oceanic Niño Index (ONI) | https://psl.noaa.gov/data/correlation/oni.data |
| ISRIC SoilGrids 2.0 | https://soilgrids.org/ |
| OpenTopoData (SRTM 30 m API) | https://www.opentopodata.org/ |
| FAO-56 Crop Evapotranspiration guidelines | https://www.fao.org/4/X0490E/X0490E00.htm |
| Official guidance 2504/TTTV-TTBVTV (19/6/2026) | https://storage-vnportal.vnpt.vn/cmu-khdn/5342/Vanban/2026.6.19-cv-chi-dao-sx-trong-trot-ung-pho-elnino-2026_-_nqmanh_19062026180253__19062026180725_signed.pdf |
| SIWRR 2026–27 salinity outlook (press report, Tiền Phong) | https://tienphong.vn/khuyen-cao-mien-tay-ung-pho-han-man-gay-gat-mua-kho-sap-toi-post1882122.tpo |
| Esri World Imagery (basemap tiles) | https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9 |
| Photon geocoder (OpenStreetMap data) | https://photon.komoot.io/ |
| OpenStreetMap contributors | https://www.openstreetmap.org/copyright |
| Solar System Scope Earth textures (CC BY 4.0) | https://www.solarsystemscope.com/textures/ |
| Wikimedia Commons crop photos (credits in `frontend/public/crops/CREDITS.md`) | https://commons.wikimedia.org/ |
| Be Vietnam Pro font (OFL) | https://fonts.google.com/specimen/Be+Vietnam+Pro |
| React | https://react.dev/ |
| Vite | https://vite.dev/ |
| MapLibre GL JS | https://maplibre.org/ |
| three.js | https://threejs.org/ |
| FastAPI | https://fastapi.tiangolo.com/ |
| Chatterbox TTS (AI voice-over, MIT) | https://github.com/resemble-ai/chatterbox |
| Kokoro-82M TTS (voice reference, Apache-2.0) | https://huggingface.co/hexgrad/Kokoro-82M |
| faster-whisper (voice-over transcription check) | https://github.com/SYSTRAN/faster-whisper |
| Claude Code (Anthropic), AI coding assistant | https://www.anthropic.com/claude-code |
| OpenAI Codex, AI coding assistant | https://openai.com/codex/ |

---

## Submission checklist

- [ ] Repository public. Check that `https://github.com/vminh16/fieldshift-mekong` opens in a logged-out browser.
- [ ] Video uploaded. Check that the link opens in a logged-out browser and the video is ≤ 30 s.
- [ ] `docs/AI_USAGE.md` TODO completed by the team.
- [ ] LICENSE chosen and added.
- [ ] Every link above opens without login.
- [ ] Terms and Conditions accepted; "all work original" confirmed (all external resources are listed above).
