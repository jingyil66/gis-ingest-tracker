# Data Sources and Acquisition Record

This file records where each raw dataset came from, when it was acquired, and
how it will be used. Raw files under `data/raw/` must not be modified in place.
Derived or standardized data belongs under `data/processed/`.

## 1. Burnaby Park Inventory

- **Dataset name:** Park Inventory
- **Publisher:** City of Burnaby
- **Source type:** ArcGIS REST Feature Layer
- **Service URL:** https://gis.burnaby.ca/arcgis/rest/services/OpenData/OpenData1/MapServer/6
- **Layer ID:** `6`
- **Published date:** 2016-09-12
- **Metadata updated:** 2017-01-20
- **Data updated:** 2023-08-25
- **Download date:** 2026-11-11
- **Downloaded format:** GeoJSON
- **Acquisition method:** Manual GeoJSON export from the City of Burnaby Open
  Data portal
- **Service-native CRS:** EPSG:26910 — NAD83 / UTM zone 10N
- **Downloaded-file CRS:** EPSG:4326
- **Local raw path:** `data/raw/burnaby/Park_Inventory.geojson`
- **Feature count at validation:** 402
- **Geometry types:** Polygon (394), MultiPolygon (8)
- **Source identifier:** `OBJECTID`
- **Important attributes:** `NAME`, `CLASSIFICATION`, `OWNERSHIP`,
  `PARK_STATUS`, `FUND_PROGRAM`
- **Purpose:** Park boundaries used for ingestion testing, QA/QC, and
  park-accessibility analysis.
- **Licence:** Open Government Licence – Burnaby
- **Portal:** https://data.burnaby.ca/
- **Required attribution:** Contains information licensed under the Open
  Government Licence – Burnaby.
- **Notes:** The source describes this layer as known parks and golf courses in
  Burnaby. One named park may contain multiple polygons.

## 2. Burnaby Street

- **Dataset name:** Street
- **Publisher:** City of Burnaby
- **Source type:** ArcGIS REST Feature Layer
- **Service URL:** https://gis.burnaby.ca/arcgis/rest/services/OpenData/OpenData5/MapServer/8
- **Layer ID:** `8`
- **Published date:** 2016-09-12
- **Metadata updated:** 2016-10-18
- **Data updated:** 2023-01-21
- **Download date:** 2026-11-11
- **Downloaded format:** GeoJSON
- **Acquisition method:** Manual GeoJSON export from the City of Burnaby Open
  Data portal
- **Service-native CRS:** EPSG:26910 — NAD83 / UTM zone 10N
- **Downloaded-file CRS:** EPSG:4326
- **Local raw path:** `data/raw/burnaby/Street.geojson`
- **Feature count at validation:** 4,804
- **Geometry types:** LineString (4,803), MultiLineString (1)
- **Source identifiers:** `OBJECTID`, `COMPKEY`
- **Important attributes:** `STREETNAME`, `STREETCLASS`,
  `STREETCLASS_desc`, `NOLANES`, `STATUS`
- **Purpose:** Road-reference layer and a second geometry type for ingestion
  and QA/QC testing.
- **Licence:** Open Government Licence – Burnaby
- **Portal:** https://data.burnaby.ca/
- **Required attribution:** Contains information licensed under the Open
  Government Licence – Burnaby.
- **Notes:** The service has a maximum record count per request. Any future
  automated downloader must implement pagination and verify the final feature
  count.

## 3. Burnaby Boundary

- **Dataset name:** Burnaby Boundary
- **Publisher:** City of Burnaby
- **Source type:** ArcGIS REST Feature Layer
- **Service URL:** https://gis.burnaby.ca/arcgis/rest/services/OpenData/OpenData3/MapServer/12
- **Layer ID:** `12`
- **Published date:** 2016-10-18
- **Metadata updated:** 2016-11-08
- **Data updated:** 2023-08-25
- **Download date:** 2026-11-11
- **Downloaded format:** GeoJSON
- **Acquisition method:** Manual GeoJSON export from the City of Burnaby Open
  Data portal
- **Service-native CRS:** EPSG:26910 — NAD83 / UTM zone 10N
- **Downloaded-file CRS:** EPSG:4326
- **Local raw path:** `data/raw/burnaby/Burnaby_Boundary.geojson`
- **Feature count at validation:** 1
- **Geometry type:** Polygon
- **Source identifier:** `OBJECTID`
- **Important attributes:** `PROJ`, `RD`, `LOCALAREA`
- **Purpose:** Defines the project study area and will be used to select or
  clip other datasets to Burnaby.
- **Licence:** Open Government Licence – Burnaby
- **Portal:** https://data.burnaby.ca/
- **Required attribution:** Contains information licensed under the Open
  Government Licence – Burnaby.

## 4. 2021 Census Dissemination Area Boundaries

- **Dataset name:** 2021 Census Dissemination Area Cartographic Boundary File
- **Publisher:** Statistics Canada
- **Catalogue number:** `92-169-X2021001`
- **Geographic level:** Dissemination Area (DA)
- **Census year:** 2021
- **Boundary type:** Cartographic Boundary File (CBF)
- **Language:** English
- **Release date:** 2021-11-17
- **Geographic reference date:** 2021-01-01
- **Official product page:** https://www150.statcan.gc.ca/n1/en/catalogue/92-169-X2021001
- **Boundary download page:** https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/index2021-eng.cfm?year=21
- **Direct download URL:** https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/files-fichiers/lda_000b21a_e.zip
- **Download date:** 2026-11-12
- **Downloaded format:** Shapefile distributed as ZIP
- **Acquisition method:** Manual ZIP download from the Statistics Canada
  boundary files page
- **Original CRS:** EPSG:3347 — NAD83 / Statistics Canada Lambert
- **Local raw path:** `data/raw/population/lda_000b21a_e.zip`
- **Feature count at validation:** 57,932
- **Geometry types:** Polygon (56,409), MultiPolygon (1,523)
- **Join fields:** `DAUID`, `DGUID`
- **Other important attributes:** `LANDAREA`, `PRUID`
- **Purpose:** Select the dissemination areas within Burnaby and join them to
  2021 Census Profile population attributes.
- **Licence:** Statistics Canada Open Licence
- **Licence URL:** https://www.statcan.gc.ca/en/reference/licence
- **Notes:** This file contains boundaries and identifiers, not population
  values. Population attributes must be acquired separately from the 2021
  Census Profile and joined using `DGUID`.

## 5. 2021 Census Profile Population

- **Dataset name:** Census Profile, 2021 Census of Population
- **Publisher:** Statistics Canada
- **Source type:** SDMX REST API
- **API guide:** https://www12.statcan.gc.ca/wds-sdw/2021profile-profil2021-eng.cfm
- **Dataflow:** `STC_CP,DF_DA,1.3`
- **Query key:** `A5.{DGUID}.1.1.1`
- **Geographic level:** Dissemination Area (DA)
- **Characteristic:** Population, 2021
- **Characteristic code:** `1`
- **Gender:** Total
- **Gender code:** `1`
- **Statistic:** Counts
- **Statistic code:** `1`
- **Release date:** 2022-02-09
- **Access date:** 2026-11-12
- **Downloaded format:** CSV
- **Local raw path:** `data/raw/population/burnaby_da_population_2021_api.csv`
- **Record count at validation:** 322
- **Unique geography count:** 322
- **Population field:** `OBS_VALUE`
- **Join relationship:** API field `REF_AREA` joins to boundary field `DGUID`
- **Population total at validation:** 249,125
- **Acquisition method:** API requests in 13 batches, with a maximum of 25
  DGUIDs per request
- **Geography selection method:** DA representative points located within the
  City of Burnaby boundary
- **Licence:** Statistics Canada Open Licence
- **Licence URL:** https://www.statcan.gc.ca/en/reference/licence
- **Notes:** The API returned no missing population values, no duplicate
  DGUIDs, and no populated `FLAG` values. The complete API response columns
  were retained in the raw CSV.

## Validation Snapshot

The following checks were performed after acquisition:

- All four raw datasets opened successfully with GeoPandas.
- Burnaby GeoJSON coordinate ranges are consistent with EPSG:4326.
- The Census DA ZIP opened directly without manual extraction.
- Every dataset contained at least one feature.
- The Census Profile CSV contains 322 records and 322 unique DGUIDs.
- The Census Profile CSV contains no missing population values or duplicate
  DGUIDs.
- The sum of the selected DA population values is 249,125.
- Detailed geometry, null-value, validity, duplicate, and schema checks will
  be generated later by the QA/QC pipeline rather than maintained manually in
  this file.
