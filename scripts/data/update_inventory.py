"""Regenerate the handoff inventory from validated artifacts and current job state (no network)."""

from __future__ import annotations

import gzip
import json
import os
from pathlib import Path

from common import DEFAULT_CACHE, ROOT, SITES, now, write_json
from observations import OBS

DEST = ROOT / "docs/data/data_inventory.json"
RES = ROOT / "apps/api/src/fieldshift/resources"


def read(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(
        gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_text()
    )


def relative(path):
    return str(Path(path).relative_to(ROOT))


def alive(pid):
    try:
        os.kill(pid, 0)
        stat = Path(f"/proc/{pid}/stat").read_text().split()
        return stat[2] != "Z"
    except (ProcessLookupError, FileNotFoundError):
        return False


def read_check(name, success):
    path = ROOT / ".fieldshift/logs" / name
    content = path.read_text() if path.exists() else ""
    result = (
        "PASS"
        if success in content and "FAILED" not in content and "failed," not in content
        else "PENDING_OR_FAILED"
    )
    return {"result": result, "log": relative(path)}


def build():
    entries = []

    def add(
        source,
        status,
        auth="none",
        notes="",
        files=None,
        what=None,
        period=None,
        latency=None,
        **extra,
    ):
        entry = {
            "source": source,
            "status": status,
            "auth": auth,
            "what_we_fetched": what or {},
            "files": files or [],
            "time_range": period,
            "latency_days": latency,
            "verified_on": now(),
            "notes": notes,
            **extra,
        }
        entries.append(entry)
        return entry

    def observed(source, folders, status="FETCHED", notes="", auth="none", **extra):
        files = [p for f in folders for p in (OBS / f).glob("*.json.gz")]
        descriptions = {}
        for p in sorted(files):
            d = read(p)
            descriptions[p.parent.name + "/" + p.name.split(".")[0]] = {
                "rows": len(d["series"]),
                "time_range": d["time_range"],
                "bytes_gz": p.stat().st_size,
                "variables": d["variables"],
                "qa_note": d["qa_note"],
            }
        ranges = [x["time_range"] for x in descriptions.values() if x["time_range"]]
        period = [min(p[0] for p in ranges), max(p[1] for p in ranges)] if ranges else None
        return add(
            source,
            status,
            auth,
            notes,
            [relative(p) for p in sorted(files)],
            descriptions,
            period=period,
            **extra,
        )

    observed(
        "NASA POWER",
        ["power"],
        notes="Existing integrated daily AG cache repackaged with fill→null. Mixed coastal meteorology cell; requested point is not verified grid center.",
        latency=4,
        integrated_files=[relative(p) for p in (RES / "demo_cache/power").glob("*")],
    )
    stages = {
        f: read(DEFAULT_CACHE / f / "progress.json", {})
        for f in ["imerg_monthly", "imerg_late", "gldas"]
    }

    for stage in stages.values():
        n, seconds = stage.get("completed", 0), stage.get("seconds", 0)
        if n:
            stage["effective_seconds_per_request"] = round(seconds / n, 3)
            stage["estimated_remaining_minutes"] = round(
                (stage.get("requested", n) - n) * seconds / n / 60, 1
            )
            stage["rate_note"] = (
                "Measured wall time/window; estimate, not a service SLA. Cached resume is faster."
            )

    def complete(stage):
        return stage.get("completed", 0) == stage.get("requested", -1)

    observed(
        "GPM IMERG",
        ["imerg_monthly", "imerg_late"],
        status="FETCHED"
        if all(complete(stages[f]) for f in ["imerg_monthly", "imerg_late"])
        else "SCRIPT_READY_NEEDS_TIME",
        auth="Earthdata netrc; IPv4 curl; private temporary cookie jar, removed on exit",
        notes="V07 Final monthly mm/hr × 24 × calendar days → mm/month; Late daily mm/day unchanged. One spatial window for four sites. POWER comparisons are period-matched; progress below distinguishes partial coverage. DAP4 metadata avoids incompatible V07B UInt64 attributes. Old gpm1 host stopped accepting connections tonight; cloud works.",
        progress={f: stages[f] for f in ["imerg_monthly", "imerg_late"]},
        latency={"monthly_final": 409, "daily_late": 1},
    )
    primary = read(DEFAULT_CACHE / "appeears/task.json", {})
    second = read(DEFAULT_CACHE / "appeears/task_thermal_hls.json", {})

    def processed(state):
        return read(
            DEFAULT_CACHE
            / "appeears/bundles"
            / state.get("task_id", "missing")
            / "processed_summary.json",
            {},
        )

    for name, folders, state, note in [
        (
            "SMAP",
            ["smap"],
            primary,
            "L4 model soil moisture surface/root zone, not measured canal salinity. Requested 2015-01-01→2026-11-10; SMAP starts 2015-03-31.",
        ),
        (
            "MODIS / VIIRS",
            ["modis_vi", "modis_et"],
            primary,
            "MOD13Q1 NDVI/EVI and MOD16A2GF actual ET. VIIRS not separately fetched. MOD16 gap-filled current year normally absent; per-composite ET is not ET0.",
        ),
        (
            "HLS",
            ["hls_l30", "hls_s30", "hls_l30_qa", "hls_s30_qa"],
            second,
            "HLSL30_VI.020/HLSS30_VI.020 NDVI plus corresponding HLSL30.020/HLSS30.020 Fmask. Point CSV already scaled. Join QA and VI by acquisition before use; no cloud interpolation.",
        ),
        (
            "ECOSTRESS",
            ["ecostress_lst", "ecostress_et"],
            second,
            "Catalog verified ECO_L2T_LSTE.002 LST/LST_err/QC/cloud and ECO_L3T_JET.002 ETdaily/cloud; requested 2023-01-01→2026-11-13. Catalog offers requested v002; do not substitute v003 silently.",
        ),
    ]:
        summary = processed(state)
        ready = all(f in summary for f in folders if not f.endswith("_qa"))
        observed(
            name,
            folders,
            status="FETCHED" if ready else "SCRIPT_READY_NEEDS_TIME",
            auth="Earthdata Basic login; token only in memory",
            notes=note
            + (
                " [UNVERIFIED] Output units, coverage and cloud/valid counts await task completion."
                if not ready
                else ""
            ),
            task_id=state.get("task_id"),
            task_status=state.get("status"),
            task_state_file=relative(
                DEFAULT_CACHE
                / "appeears"
                / ("task.json" if state == primary else "task_thermal_hls.json")
            ),
            latency=None,
            requested_time_range=[
                state["request"]["params"]["dates"][0]["startDate"],
                state["request"]["params"]["dates"][0]["endDate"],
            ],
        )
    observed(
        "GLDAS",
        ["gldas"],
        status="FETCHED" if complete(stages["gldas"]) else "SCRIPT_READY_NEEDS_TIME",
        auth="Earthdata netrc, IPv4 curl",
        notes="Data Rods endpoint returns HTML, not series; NASA explicitly discontinued service. No GLDAS in AppEEARS catalog. Successful alternate fallback: GLDAS_NOAH025_M v2.1 cloud OPeNDAP, 4 variables, monthly means 2001→2026-07. This does NOT provide 3-hourly data. Soil water kg/m2 divided by layer depth and water density; flux integrated over calendar month. No current-state claim.",
        progress=stages["gldas"],
        latency=105,
        coverage_evidence=[
            {
                "url": "https://github.com/nasa/gesdisc-tutorials/blob/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md",
                "summary": "NASA migration notice lists Hydrology Data Rods among discontinued services.",
            }
        ],
        probe_file=".fieldshift/cache/gldas_probe.json",
    )
    observed(
        "SRTM / NASADEM",
        ["srtm"],
        notes="Existing SRTM via OpenTopoData inspected and repackaged; NASADEM not independently fetched. Static mission February 2000; vertical precision inadequate for field-scale inundation thresholds.",
        latency=None,
        integrated_files=[relative(p) for p in (RES / "demo_cache/srtm").glob("*")],
    )
    observed(
        "FAO GAEZ v4",
        ["gaez"],
        notes="Programmatic FAO ArcGIS res05 and LR ImageServer identify, with locked raster IDs and renderingRule None. Four crops wetland rice/maize/soybean/groundnut; rainfed all-land indices plus irrigated current-cropland indices, high/low input, and soil constraints. 41 layers/site. Mungbean absent; no substitution. Static prior, not current soil measurement.",
        latency=None,
        coverage_evidence=[
            {
                "url": "https://www.fao.org/gaez/gaezv4/en",
                "summary": "GAEZ v4 global 5 arc-minute suitability for 51 crops, baseline 2010 and historical climate.",
            }
        ],
        layer_catalog=".fieldshift/cache/gaez/selected_layers.json",
        service_url="https://gaez-services.fao.org/server/rest/services/",
    )
    snapshots = read(ROOT / "docs/data/images/manifest.json", [])
    add(
        "NASA Worldview Snapshots",
        "FETCHED" if len(snapshots) == 12 else "SCRIPT_READY_NEEDS_TIME",
        notes="Pitch browse images only. EPSG:4326 snapshot BBOX uses latitude,longitude axis order; intended lon/lat bounds [104.4,8.5,106.9,11.2]. NDVI uses MODIS Terra L3 16-day product and aligned composite dates. Transparent dry-season rain image cannot distinguish zero from missing by itself; no quantitative inference. See image README for visual checks.",
        files=[s["file"] for s in snapshots],
        what={
            "images": len(snapshots),
            "bytes": sum(s["bytes"] for s in snapshots),
            "snapshots": snapshots,
        },
        period=["2016-03", "2024-09"],
        latency=None,
    )
    gedi = {s: read(DEFAULT_CACHE / "gedi" / (s + ".json"), {}) for s in SITES}
    add(
        "GEDI L4A",
        "NOT_USEFUL_HERE",
        auth="CMR public; footprints require Earthdata",
        notes="CMR bbox intersections are granule-level coverage only, NOT proof that a laser footprint hits a demo field. Latest L4A V3 collection C4212593885-ORNL_CLOUD. ±0.005° site windows. [UNVERIFIED] Exact footprint intersection and biomass QA not inspected. Sparse woody-biomass sampling is unsuitable for rice-rotation state.",
        files=[f".fieldshift/cache/gedi/{s}.json" for s in SITES],
        what={
            s: {"intersecting_granules": g.get("cmr_hits"), "query_url": g.get("url")}
            for s, g in gedi.items()
        },
    )
    add(
        "Sentinel-2",
        "FETCHED" if processed(second).get("hls_s30") else "SCRIPT_READY_NEEDS_TIME",
        auth="Earthdata via AppEEARS",
        notes="Covered via HLSS30 / HLSS30_VI; no separate Sentinel-2 L2A download.",
        what={"task_id": second.get("task_id")},
        files=[relative(p) for p in (OBS / "hls_s30").glob("*")],
    )
    observed(
        "ERA5 via Open-Meteo",
        ["era5_openmeteo"],
        notes="Explicit models=era5, UTC, nearest grid, elevation=nan (no downscaling); daily Tmax/Tmin/precipitation/FAO ET0. Four sites, no CDS auth. Recent ERA5T preliminary. POWER comparisons in headers. Completed after transient 429 retry.",
        latency=5,
        license="CC BY 4.0 Open-Meteo; Copernicus attribution",
    )
    # Existing integrations: report actual payloads, including empty SoilGrids data.
    soil = {s: read(RES / "demo_cache/soilgrids" / (s + ".json")) for s in SITES}
    add(
        "SoilGrids",
        "FETCHED",
        notes="Existing integration/cache only. All 4 site files contain null clay/sand/pH/SOC at both depths: ZERO usable measurements. Runtime fallback is an ASSUMPTION, never observations. GAEZ provides independent static soil constraints. [UNVERIFIED] SoilGrids service recovery not tested tonight.",
        files=[relative(p) for p in (RES / "demo_cache/soilgrids").glob("*")],
        what={
            "sites": 4,
            "usable_measurements": sum(
                v is not None
                for s in soil.values()
                for d in s["properties"].values()
                for v in d.values()
            ),
            "properties": ["clay", "sand", "phh2o", "soc"],
            "depths": ["0-5cm", "15-30cm"],
        },
    )
    for source, folder in [("Open-Meteo seasonal", "seasonal"), ("GloFAS", "glofas")]:
        files = list((RES / "demo_cache" / folder).glob("*.gz"))
        info = {}
        for p in files:
            d = read(p)
            payload = d["payload"]
            daily = payload["daily"]
            times = daily["time"]
            info[p.stem] = {
                "rows": len(times),
                "time_range": [times[0], times[-1]],
                "variables": len(daily) - 1,
                "retrieved_at": d.get("retrieved_at"),
            }
        add(
            source,
            "FETCHED",
            notes="Existing integrated responses inspected locally. "
            + (
                "ECMWF SEAS5 ensemble, uncalibrated locally; forecast probabilities not independently verified."
                if folder == "seasonal"
                else "Tan Chau modeled regional discharge, not field salinity. Includes 2001–2020 daily reference and recent/7-day forecast."
            ),
            files=[relative(p) for p in files],
            what=info,
            period=[
                min(v["time_range"][0] for v in info.values()),
                max(v["time_range"][1] for v in info.values()),
            ],
            latency={
                "model_updates": "monthly" if folder == "seasonal" else "daily",
                "observational_latency": None,
            },
        )
    info = {}
    nexfiles = list((RES / "projections").glob("*.json"))
    for p in nexfiles:
        d = read(p)
        info[p.stem] = {
            "series": len(d["series"]),
            "monthly_values": sum(len(s["values"]) for s in d["series"]),
            "period": d["period"],
        }
    ready = len(info) == 4 and all(x["monthly_values"] == 2496 for x in info.values())
    add(
        "NEX-GDDP-CMIP6",
        "FETCHED" if ready else "SCRIPT_READY_NEEDS_TIME",
        notes="v2.0 ACCESS-CM2/MPI-ESM1-2-HR × SSP245/585 × tasmax/pr. 2025–2050. CSV units checked K→degC, kg m-2 s-1→mm/day, complete calendar-month aggregation. Completed site files automatically replace bundled projections atomically; 4 scenarios/site. No SSP probabilities.",
        files=[relative(p) for p in nexfiles],
        what=info,
        period=["2025-01", "2050-12"],
        latency=None,
    )
    excluded = [
        (
            "WSS",
            "https://www.nrcs.usda.gov/resources/data-and-reports/soil-survey-geographic-database-ssurgo",
            "NRCS soil surveys cover the US and served territories/island nations, not Vietnam.",
            "SoilGrids (currently empty), GAEZ soil constraints; farmer soil data",
        ),
        (
            "CDL",
            "https://data.nass.usda.gov/Research_and_Science/Cropland/sarsfaqs2.php",
            "USDA Cropland Data Layer maps US cropland.",
            "HLS NDVI and MODIS seasonal vegetation cycles",
        ),
        (
            "PRISM",
            "https://prism.oregonstate.edu/documents/PRISM_downloads_web_service.pdf",
            "PRISM service us domain is the conterminous 48 states.",
            "POWER and ERA5 via Open-Meteo",
        ),
        (
            "SSURGO / STATSGO2",
            "https://www.nrcs.usda.gov/conservation-basics/soil/tabular-data-query-tools",
            "STATSGO2 inventory is continental US, Hawaii, Alaska, Puerto Rico and Virgin Islands; no Vietnam.",
            "GAEZ static soil constraints; SoilGrids when available",
        ),
        (
            "NAIP",
            "https://www.usgs.gov/national-map-supporting-themes",
            "National Map NAIP aerial imagery covers conterminous United States.",
            "HLS Landsat/Sentinel-2 and MODIS true color",
        ),
        (
            "NLCD",
            "https://www.usgs.gov/centers/eros/science/annual-national-land-cover-database",
            "Annual NLCD science products cover conterminous United States.",
            "HLS/GAEZ land-cover context; ESA WorldCover not fetched",
        ),
        (
            "NLDAS",
            "https://ntrs.nasa.gov/api/citations/20220018556/downloads/AGU2022_HDISC.pdf",
            "Domain 25–53N and 125–67W excludes Vietnam; parts of Canada/Mexico included.",
            "GLDAS Noah 2.1 / SMAP",
        ),
        (
            "CoCoRaHS",
            "https://www.cocorahs.org/default.aspx",
            "Network countries include US, Canada and Bahamas plus listed territories; no Vietnam network.",
            "IMERG, POWER, ERA5; farmer rain gauges",
        ),
        (
            "NWIS",
            "https://waterdata.usgs.gov/?redirect=nwis_w_redirect",
            "USGS monitoring program covers US states/territories and some border sites; no verified Mekong demo gauges.",
            "GloFAS modeled Mekong discharge; farmer ECw (no salinity inference)",
        ),
        (
            "NASS QuickStats",
            "https://www.nass.usda.gov/Quick_Stats/",
            "NASS agriculture statistics for US agriculture, not Vietnam local farm statistics.",
            "Farmer-entered prices; economic model disabled",
        ),
        (
            "OpenET",
            "https://openet.gitbook.io/docs/additional-resources/change-log",
            "OpenET asset v2.1+ covers 48 contiguous US states (broader than old western-US description), not Vietnam.",
            "MOD16 ET, ECOSTRESS ET, POWER/ERA5 ET0",
        ),
        (
            "LANDFIRE",
            "https://www.landfire.gov/data/lf2025",
            "US vegetation/fuels mapping; not Vietnam.",
            "HLS NDVI, GAEZ land/soil context",
        ),
    ]
    for name, url, claim, alternative in excluded:
        add(
            name,
            "NOT_AVAILABLE_FOR_VIETNAM",
            notes=claim,
            what={"rows": 0},
            alternative=alternative,
            coverage_evidence=[
                {
                    "url": url,
                    "summary": claim,
                    "verification": "official coverage statement checked 2026-11-13",
                }
            ],
        )
    add(
        "AMS Market News",
        "NOT_USEFUL_HERE",
        notes="Correction to US-only premise: AMS also reports international market information. No verified local Mekong farm-gate price series obtained. Absence of all Vietnam data cannot be established. [UNVERIFIED] Vietnam-specific commodity report coverage.",
        what={"rows": 0},
        alternative="Farmer-entered prices; economic model disabled",
        coverage_evidence=[
            {
                "url": "https://www.usda.gov/sites/default/files/documents/24-2023-AMS.pdf",
                "summary": "USDA explanatory notes describe domestic and international market reporting.",
            }
        ],
    )
    add(
        "USDA Ag Data Commons",
        "NOT_USEFUL_HERE",
        notes="Correction to US-only premise: this is a USDA-funded research repository, not a US-bounded raster product. It can contain international/global studies. No suitable demo-site observation dataset selected; NOT_AVAILABLE_FOR_VIETNAM would be unsupported.",
        what={"rows": 0},
        alternative="GAEZ suitability, POWER/ERA5 climate; FAO crop parameter catalog",
        coverage_evidence=[
            {
                "url": "https://www.nal.usda.gov/services/agdatacommons",
                "summary": "Repository eligibility is based on USDA affiliation/funding; no US-only geographic restriction.",
            }
        ],
    )
    add(
        "ERA5 CDS",
        "SCRIPT_READY_NEEDS_TIME",
        auth="Separate CDS account/PAT + accepted dataset licence; Earthdata credentials do not apply",
        notes="Existing fetch_era5_cds.py available, not run tonight because the requested no-auth ERA5 Open-Meteo path is complete. Do not count the CDS script as a downloaded CDS dataset.",
        files=["scripts/data/fetch_era5_cds.py"],
        alternative="ERA5 via Open-Meteo",
    )
    add(
        "GRACE / GRACE-FO",
        "NOT_USEFUL_HERE",
        auth="Earthdata",
        notes="Listed in project context but not required for tonight. Basin-scale storage anomaly (~300 km effective) cannot resolve four nearby rice fields. [UNVERIFIED] No granules/pixels fetched tonight.",
        what={"rows": 0},
        alternative="GLDAS soil water, SMAP; GloFAS regional discharge",
    )
    jobs = read(DEFAULT_CACHE / "jobs.json", [])
    for job in jobs:
        job["running"] = alive(job["pid"])
    value = {
        "schema_version": 1,
        "generated_at": now(),
        "worktree": str(ROOT),
        "branch": "exp/api",
        "scope": "Superset of every named challenge source and extras; SSURGO/STATSGO2 and MODIS/VIIRS grouped. Status FETCHED describes artifact acquisition, not guaranteed usable measurements; inspect notes and counts.",
        "status_values": [
            "FETCHED",
            "SCRIPT_READY_NEEDS_TIME",
            "NOT_AVAILABLE_FOR_VIETNAM",
            "NOT_USEFUL_HERE",
            "MANUAL_DOWNLOAD",
        ],
        "sites": SITES,
        "sources": entries,
        "jobs": jobs,
        "verification": {
            "make_test_result": read_check("make-test.log", "passed"),
            "ruff_check_result": read_check("ruff-check.log", "All checks passed!"),
            "ruff_format_result": read_check("ruff-format.log", "already formatted"),
            "independent_nex_check_log": ".fieldshift/logs/verify-data-access.log",
            "observation_check_log": ".fieldshift/logs/verify-observations.log",
            "make_test_log": ".fieldshift/logs/make-test.log",
            "ruff_check_log": ".fieldshift/logs/ruff-check.log",
            "ruff_format_log": ".fieldshift/logs/ruff-format.log",
        },
        "refresh_command": ". .venv/bin/activate && python scripts/data/update_inventory.py",
    }
    write_json(DEST, value)
    return value


if __name__ == "__main__":
    value = build()
    print("inventory", len(value["sources"]), "sources", len(value["jobs"]), "jobs")
