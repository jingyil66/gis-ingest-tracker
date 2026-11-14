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

Burnaby’s 2021 population in this extract is 249,125. Census Dissemination Areas were selected based on whether their representative points fall within the Burnaby municipal boundary. Some selected polygons extend beyond the municipal boundary; spatial coverage calculations use the full selected DA polygons rather than clipping them to the municipal boundary.

Acquisition dates, licences, and raw paths are in `sources.md`.

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

## Area measures

Population density and park coverage use different areas on purpose. That difference is not a calculation error. The two measures answer different questions.

Population density uses Statistics Canada’s official land area so that water is not included in the denominator. In the 2021 DA boundary file this is `LANDAREA`, stored as `land_area_km2`, in square kilometres. The 2021 population count is divided by that land area:

```text
population_density_km2 = population_2021 / land_area_km2
```

For the whole extract, 249,125 people divided by 90.57 km² of land area gives about 2,751 people per km². The value 4,553 is not this citywide density. It is the median of the 322 DA densities. Dividing 249,125 by 4,553 gives about 54.7, but 54.7 km² is not the land area of these DAs.

Park coverage uses the full DA polygon in EPSG:26910 so that the buffer overlap is the share of that mapped polygon. Both the numerator and the denominator are planar polygon areas in square metres. Water is not removed from either one. The polygons are not clipped to the municipal boundary before this ratio is calculated. `area(DA polygon)` can differ from `land_area_km2`, although for most of these DAs the two are close.

```text
park_coverage_pct = 100 * area(DA ∩ 400 m park buffer) / area(DA polygon)
```

`area(DA ∩ 400 m park buffer)` is the field `intersect_area`. A DA with no overlap is treated as 0. The 400-metre buffer is a straight-line distance from the repaired park boundaries.

## Maps

The QGIS project is `burnaby_park_access.qgz`. Exported pages:

| File | What it shows |
|---|---|
| `population_distribution.pdf` | 2021 population density (people per km²) by DA, with parks |
| `park_accessibility.pdf` | Percent of each DA polygon inside the 400 m park buffer |
| `park_priority.pdf` | Screening classes from density and that coverage percent |

Most DAs touch the 400-metre area, so a simple inside-or-outside flag hides the difference. The accessibility map uses `park_coverage_pct` above.

The priority map is a preliminary screen. It is not a verified park-service gap and it is not a formal public-service ranking. Higher density means `population_density_km2` at or above 4,553, the median of these 322 DA densities. Lower coverage means `park_coverage_pct` below 80. The class that meets both is labeled **High Screening Priority** in the QGIS project. Re-export `park_priority.pdf` after opening the project so the file matches that label.

## Limits

The 400-metre distance is a straight line from the park boundary, not a walking route. Rivers, highways, and entrances are not considered.

`park_coverage_pct` uses the DA polygon area, not `land_area_km2`, and it is not the share of residents who can reach a park. People may live in the part of a DA that is farther from a park.

The screening class marks areas to look at first. It does not show a proven shortage of park service, and it is not a formal ranking of public-service priority.
