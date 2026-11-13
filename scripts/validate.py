from pathlib import Path
import sys

import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from database import (
    DB_PATH,
    add_history,
    clear_tracker,
    init_db,
    set_status,
    upsert_dataset,
)


GPKG_PATH = PROJECT_ROOT / "data" / "processed" / "burnaby_gis.gpkg"
GPKG_DISPLAY = "data/processed/burnaby_gis.gpkg"
REPORTS_DIR = PROJECT_ROOT / "reports"
QC_REPORT_PATH = REPORTS_DIR / "qc_report.csv"
TARGET_EPSG = 26910

REQUIRED_FIELDS = {
    "parks": [
        "source_object_id",
        "park_name",
        "geometry",
    ],
    "roads": [
        "source_object_id",
        "street_name",
        "geometry",
    ],
    "municipal_boundary": [
        "source_object_id",
        "local_area",
        "geometry",
    ],
    "census_da_population": [
        "dguid",
        "population_2021",
        "geometry",
    ],
}

DATASET_META = {
    "parks": {
        "source": "City of Burnaby Open Data — Park Inventory",
        "received_date": "2026-11-11",
    },
    "roads": {
        "source": "City of Burnaby Open Data — Street",
        "received_date": "2026-11-11",
    },
    "municipal_boundary": {
        "source": "City of Burnaby Open Data — Burnaby Boundary",
        "received_date": "2026-11-11",
    },
    "census_da_population": {
        "source": "Statistics Canada 2021 DA boundaries + Census Profile API",
        "received_date": "2026-11-12",
    },
}


def qc_layer(gdf, layer_name):
    fields = REQUIRED_FIELDS[layer_name]
    missing_required = [
        field for field in fields if field not in gdf.columns
    ]

    attribute_fields = [
        field
        for field in fields
        if field != "geometry" and field in gdf.columns
    ]

    null_geometry = int(gdf.geometry.isna().sum())
    empty_geometry = int(gdf.geometry.is_empty.sum())
    invalid_geometry = int((~gdf.geometry.is_valid).sum())
    missing_value_count = int(gdf[attribute_fields].isna().sum().sum())

    id_field = fields[0]
    duplicate_id_count = 0
    if id_field in gdf.columns:
        duplicate_id_count = int(gdf[id_field].duplicated().sum())

    crs_ok = gdf.crs is not None and gdf.crs.to_epsg() == TARGET_EPSG

    critical_fail = (
        not crs_ok
        or null_geometry > 0
        or empty_geometry > 0
        or bool(missing_required)
        or duplicate_id_count > 0
    )

    return {
        "dataset_name": layer_name,
        "feature_count": len(gdf),
        "crs": str(gdf.crs),
        "crs_ok": crs_ok,
        "null_geometry_count": null_geometry,
        "empty_geometry_count": empty_geometry,
        "invalid_geometry_count": invalid_geometry,
        "missing_value_count": missing_value_count,
        "duplicate_id_count": duplicate_id_count,
        "missing_required_fields": (
            ";".join(missing_required) if missing_required else ""
        ),
        "overall_result": "FAILED" if critical_fail else "PASSED",
    }


def record_layer(layer_name, gdf, result):
    meta = DATASET_META[layer_name]
    feature_count = result["feature_count"]

    dataset_id = upsert_dataset(
        dataset_name=layer_name,
        source=meta["source"],
        received_date=meta["received_date"],
        current_status="RECEIVED",
        feature_count=feature_count,
    )
    add_history(
        dataset_id=dataset_id,
        operation="ingest_loaded",
        result="RECEIVED",
        message=(
            f"Loaded from {GPKG_PATH.name}; features={feature_count}"
        ),
    )

    set_status(dataset_id, "VALIDATING", feature_count)
    add_history(
        dataset_id=dataset_id,
        operation="qc_start",
        result="VALIDATING",
        message="Started geometry and attribute QC",
    )

    qc_result = result["overall_result"]
    set_status(dataset_id, qc_result, feature_count)
    add_history(
        dataset_id=dataset_id,
        operation="qc_complete",
        result=qc_result,
        message=(
            f"invalid={result['invalid_geometry_count']}; "
            f"missing={result['missing_value_count']}"
        ),
    )

    if qc_result == "PASSED":
        set_status(dataset_id, "LOADED", feature_count)
        add_history(
            dataset_id=dataset_id,
            operation="gpkg_ready",
            result="LOADED",
            message=f"Available in {GPKG_DISPLAY}",
        )

    return dataset_id


def main():
    if not GPKG_PATH.exists():
        raise FileNotFoundError(f"Missing GPKG: {GPKG_PATH}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    init_db(DB_PATH)
    clear_tracker(DB_PATH)

    qc_rows = []

    for layer_name in REQUIRED_FIELDS:
        gdf = gpd.read_file(GPKG_PATH, layer=layer_name)
        result = qc_layer(gdf, layer_name)
        dataset_id = record_layer(layer_name, gdf, result)
        qc_rows.append(result)
        print(
            layer_name,
            dataset_id,
            result["feature_count"],
            result["overall_result"],
        )

    qc_report = pd.DataFrame(qc_rows)
    qc_report.to_csv(QC_REPORT_PATH, index=False)
    print(f"Wrote {QC_REPORT_PATH}")
    print(f"Wrote {DB_PATH}")


if __name__ == "__main__":
    main()
