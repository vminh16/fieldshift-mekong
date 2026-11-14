# Mekong Delta pitch images

Twelve PNG browse images, total **4.36 MB**, from NASA Worldview Snapshots/GIBS. Bounds: longitude 104.4–106.9, latitude 8.5–11.2; north is up. The exact snapshot URL, layer, date and byte count for every image are in [manifest.json](manifest.json).

| Pitch period | True color / precipitation date | NDVI composite start |
|---|---|---|
| Dry season 2016 | 2016-03-16 | 2016-03-05 |
| Dry season 2020 | 2020-03-15 | 2020-03-05 |
| Dry season 2024 | 2024-03-15 | 2024-03-05 |
| Wet season 2024 | 2024-09-15 | 2024-09-13 |

True color is MODIS Terra corrected reflectance. The 2016-03-16 true color, March 2024 NDVI and September 2024 precipitation images were visually inspected. Clouds remain visible; these are regional illustrations. The original 2016-03-15 pass covered only a narrow edge of the box, so the following day was selected.

NDVI is **MODIS Terra L3 16-day**, not the near-real-time 8-day layer (which does not cover these historical dates). Use the [NASA NDVI legend](https://gibs.earthdata.nasa.gov/legends/MODIS_L3_NDVI_H.svg).

Precipitation is the GIBS **IMERG Precipitation Rate** browse layer. Use the [NASA precipitation legend](https://gibs.earthdata.nasa.gov/legends/GPM_Precipitation_Rate_H.svg). The fully transparent 2020 dry-season rain image has no visible signal: transparency alone cannot distinguish zero precipitation from missing imagery. **Do not turn screenshot colors/transparency into quantitative rain totals**; use the processed IMERG point series instead.

`EPSG:4326` in the Snapshot API uses **latitude,longitude** axis order: `BBOX=8.5,104.4,11.2,106.9`. Longitude-first input returns an empty image. The manifest also records the intended longitude/latitude bounds explicitly.

Attribution: NASA Worldview, NASA EOSDIS Global Imagery Browse Services (GIBS), MODIS Terra and GPM IMERG. Recreate with `. .venv/bin/activate && python scripts/data/fetch_worldview.py`.
