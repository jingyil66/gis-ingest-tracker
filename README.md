# Burnaby park accessibility and population

This project ingests City of Burnaby open data and 2021 Census geography for Burnaby, checks the layers, and maps where people live relative to parks.

It answers three questions:

1. Where is population density higher or lower?
2. How much of each dissemination area (DA) lies within 400 metres of a park, measured as a straight line?
3. Which areas are both relatively dense and less covered by that 400-metre distance?

The maps were made in QGIS. 

## Data

| Layer | Source | Features |
|---|---|---|
| Parks | City of Burnaby Open Data, Park Inventory | 402 |
| Roads | City of Burnaby Open Data, Street | 4,804 |
| Municipal boundary | City of Burnaby Open Data | 1 |
| Census DAs and 2021 population | Statistics Canada DA boundary file and Census Profile API | 322 |

Burnaby’s 2021 population in this extract is 249,125. Acquisition dates, licences, and raw paths are in `sources.md`.

Contains information licensed under the Open Government Licence – Burnaby. Census data are used under the Statistics Canada Open Licence.

Raw files in `data/raw/` are kept unchanged. Standardized layers are written to `data/processed/burnaby_gis.gpkg` in EPSG:26910 (NAD83 / UTM zone 10N). Metres are required so that a buffer distance of 400 is 400 metres.

## Run the pipeline

Use Python 3.11 and the packages in `requirements.txt`.

```powershell
pip install -r requirements.txt
python scripts/ingest.py
python scripts/validate.py
```

`scripts/ingest.py` reads the raw layers, projects them to EPSG:26910, and writes the GeoPackage.

`scripts/validate.py` checks each layer and rebuilds `data/processed/burnaby_tracker.sqlite`. Running it again replaces the tracker rows, so the history does not grow on every run. It also rewrites `reports/qc_report.csv`.

## Quality checks

Each layer is checked for CRS, null geometries, empty geometries, invalid geometries, missing required values, duplicate IDs, and missing required fields.

A layer fails if the CRS is not EPSG:26910, a geometry is null or empty, a required field is missing, or an ID is duplicated. Invalid geometries and missing attribute values are recorded, but they do not by themselves fail the layer.

Parks passed with two warnings: two invalid polygons (Bell Park and Powerhouse Park, both self-intersections) and one missing park name (a public walkway easement). The raw park file was not edited. A repaired copy, `data/processed/parks_fixed.gpkg`, was used for the buffer and the maps.

## Processing tracker

`data/processed/burnaby_tracker.sqlite` has two tables.

`datasets` stores one current row per layer: source, date received, feature count, and status.

`processing_history` stores each step. The status order is:

`RECEIVED` → `VALIDATING` → `PASSED` or `FAILED` → `LOADED`

`PASSED` means the quality check had no failing condition. `LOADED` means the layer is in the GeoPackage and can be used. Parks reached `LOADED` with the warning `invalid=2; missing=1` kept in the history message.

## Maps

The QGIS project is `burnaby_park_access.qgz`. Exported pages:

| File | What it shows |
|---|---|
| `population_distribution.pdf` | 2021 population density (people per km²) by DA, with parks |
| `park_accessibility.pdf` | Percent of each DA’s land area within 400 m of a park |
| `park_priority.pdf` | DAs that are both relatively dense and less covered |

Most DAs touch the 400-metre area, so a simple inside-or-outside flag hides the difference. The accessibility map uses the share of each DA’s land inside the buffer. Coverage below 80 percent is treated as lower coverage. Density at or above 4,553 people per km², the median of these 322 DAs, is treated as higher density. **High Priority** means both: density at or above that median, and less than 80 percent of the DA area inside the buffer.

## Limits

The 400-metre distance is a straight line from the park boundary, not a walking route. Rivers, highways, and entrances are not considered.

`park_coverage_pct` is land area, not the share of residents who can reach a park. People may live in the part of a DA that is farther from a park.

High Priority marks areas to look at first. It does not by itself show a proven shortage of park service.
