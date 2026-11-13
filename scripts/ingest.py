from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio


TARGET_CRS = "EPSG:26910"

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_GPKG = PROCESSED_DIR / "burnaby_gis.gpkg"

PARKS_PATH = RAW_DIR / "burnaby" / "Park_Inventory.geojson"
ROADS_PATH = RAW_DIR / "burnaby" / "Street.geojson"
BOUNDARY_PATH = RAW_DIR / "burnaby" / "Burnaby_Boundary.geojson"
DA_PATH = RAW_DIR / "population" / "lda_000b21a_e.zip"
POPULATION_PATH = (
    RAW_DIR
    / "population"
    / "burnaby_da_population_2021_api.csv"
)


def require_columns(dataframe, required_columns, dataset_name):
    missing_columns = sorted(
        set(required_columns) - set(dataframe.columns)
    )

    if missing_columns:
        raise ValueError(
            f"{dataset_name} is missing required columns: "
            f"{missing_columns}"
        )


def read_spatial_layer(path, dataset_name):
    if not path.exists():
        raise FileNotFoundError(
            f"{dataset_name} not found: {path}"
        )

    gdf = gpd.read_file(path)

    if gdf.crs is None:
        raise ValueError(
            f"{dataset_name} has no CRS: {path}"
        )

    if gdf.empty:
        raise ValueError(
            f"{dataset_name} contains no features: {path}"
        )

    return gdf


def project_layer(gdf, dataset_name):
    before_count = len(gdf)
    before_crs = gdf.crs
    projected = gdf.to_crs(TARGET_CRS)

    if len(projected) != before_count:
        raise ValueError(
            f"{dataset_name}: feature count changed from "
            f"{before_count} to {len(projected)}"
        )

    print(
        f"Projected {dataset_name}: "
        f"{before_crs} -> {projected.crs}; "
        f"features={len(projected)}"
    )

    return projected


def prepare_parks():
    parks = read_spatial_layer(
        PARKS_PATH,
        "parks",
    )

    required_columns = [
        "OBJECTID",
        "NAME",
        "CLASSIFICATION",
        "OWNERSHIP",
        "PARK_STATUS",
        "FUND_PROGRAM",
        "geometry",
    ]
    require_columns(parks, required_columns, "parks")

    parks = project_layer(parks, "parks")
    parks = (
        parks[required_columns]
        .rename(
            columns={
                "OBJECTID": "source_object_id",
                "NAME": "park_name",
                "CLASSIFICATION": "classification",
                "OWNERSHIP": "ownership",
                "PARK_STATUS": "park_status",
                "FUND_PROGRAM": "fund_program",
            }
        )
        .copy()
    )

    parks["perimeter_m"] = parks.geometry.length
    parks["area_m2"] = parks.geometry.area

    return parks


def prepare_roads():
    roads = read_spatial_layer(
        ROADS_PATH,
        "roads",
    )

    required_columns = [
        "OBJECTID",
        "COMPKEY",
        "STREETNAME",
        "STREETNAMEC",
        "STREETTYPE",
        "STREETDIRCODE",
        "STREETCLASS",
        "STREETCLASS_desc",
        "NOLANES",
        "SERVSTAT",
        "JURISDICTION_desc",
        "SURFWID",
        "MUNICIPALITY",
        "STATUS",
        "TRUCKROUTE",
        "DISASTERROUTE_desc",
        "geometry",
    ]
    require_columns(roads, required_columns, "roads")

    roads = project_layer(roads, "roads")
    roads = (
        roads[required_columns]
        .rename(
            columns={
                "OBJECTID": "source_object_id",
                "COMPKEY": "component_key",
                "STREETNAME": "street_name",
                "STREETNAMEC": "street_name_complete",
                "STREETTYPE": "street_type",
                "STREETDIRCODE": "street_direction_code",
                "STREETCLASS": "street_class",
                "STREETCLASS_desc": (
                    "street_class_description"
                ),
                "NOLANES": "number_of_lanes",
                "SERVSTAT": "service_status",
                "JURISDICTION_desc": (
                    "jurisdiction_description"
                ),
                "SURFWID": "surface_width",
                "MUNICIPALITY": "municipality",
                "STATUS": "status",
                "TRUCKROUTE": "truck_route",
                "DISASTERROUTE_desc": (
                    "disaster_route_description"
                ),
            }
        )
        .copy()
    )

    roads["length_m"] = roads.geometry.length

    return roads


def prepare_municipal_boundary():
    boundary = read_spatial_layer(
        BOUNDARY_PATH,
        "municipal_boundary",
    )

    required_columns = [
        "OBJECTID",
        "RD",
        "LOCALAREA",
        "geometry",
    ]
    require_columns(
        boundary,
        required_columns,
        "municipal_boundary",
    )

    boundary = project_layer(
        boundary,
        "municipal_boundary",
    )
    boundary = (
        boundary[required_columns]
        .rename(
            columns={
                "OBJECTID": "source_object_id",
                "RD": "regional_district",
                "LOCALAREA": "local_area",
            }
        )
        .copy()
    )

    boundary["perimeter_m"] = boundary.geometry.length
    boundary["area_m2"] = boundary.geometry.area

    return boundary


def prepare_census_da_population(municipal_boundary):
    da_all = read_spatial_layer(
        DA_PATH,
        "census_da_boundary",
    )
    require_columns(
        da_all,
        [
            "DGUID",
            "DAUID",
            "LANDAREA",
            "PRUID",
            "geometry",
        ],
        "census_da_boundary",
    )

    da_bc = da_all.loc[
        da_all["PRUID"] == "59"
    ].copy()
    da_bc = project_layer(
        da_bc,
        "bc_census_da",
    )

    burnaby_geometry = (
        municipal_boundary.geometry.union_all()
    )
    inside_burnaby = (
        da_bc.geometry
        .representative_point()
        .within(burnaby_geometry)
    )

    burnaby_da = (
        da_bc.loc[
            inside_burnaby,
            [
                "DGUID",
                "DAUID",
                "LANDAREA",
                "PRUID",
                "geometry",
            ],
        ]
        .rename(
            columns={
                "DGUID": "dguid",
                "DAUID": "da_uid",
                "LANDAREA": "land_area_km2",
                "PRUID": "province_uid",
            }
        )
        .copy()
    )
    burnaby_da["dguid"] = (
        burnaby_da["dguid"].astype("string")
    )

    if burnaby_da.empty:
        raise ValueError(
            "Burnaby DA selection returned no features"
        )

    if not POPULATION_PATH.exists():
        raise FileNotFoundError(
            f"Population CSV not found: {POPULATION_PATH}"
        )

    population = pd.read_csv(
        POPULATION_PATH,
        dtype={
            "REF_AREA": "string",
            "ALT_GEO_CODE": "string",
            "FLAG": "string",
        },
    )
    population_columns = [
        "REF_AREA",
        "OBS_VALUE",
        "FLAG",
        "DATA_QUALITY_FLAG",
        "TNR_LF",
        "TNR_SF",
    ]
    require_columns(
        population,
        population_columns,
        "census_population",
    )

    population = (
        population[population_columns]
        .rename(
            columns={
                "REF_AREA": "dguid",
                "OBS_VALUE": "population_2021",
                "FLAG": "census_flag",
                "DATA_QUALITY_FLAG": (
                    "data_quality_flag"
                ),
                "TNR_LF": (
                    "total_non_response_long_form"
                ),
                "TNR_SF": (
                    "total_non_response_short_form"
                ),
            }
        )
        .copy()
    )

    census_da_population = burnaby_da.merge(
        population,
        on="dguid",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    if not (
        census_da_population["_merge"] == "both"
    ).all():
        unmatched_count = int(
            (
                census_da_population["_merge"]
                != "both"
            ).sum()
        )
        raise ValueError(
            f"{unmatched_count} Burnaby DA features did "
            "not match population data"
        )

    if census_da_population[
        "population_2021"
    ].isna().any():
        raise ValueError(
            "Population contains missing values"
        )

    if (
        census_da_population["land_area_km2"] <= 0
    ).any():
        raise ValueError(
            "Census DA contains invalid land area"
        )

    census_da_population[
        "population_density_km2"
    ] = (
        census_da_population["population_2021"]
        / census_da_population["land_area_km2"]
    )
    census_da_population = (
        census_da_population
        .drop(columns="_merge")
    )

    print(
        "Joined census DA population: "
        f"features={len(census_da_population)}; "
        "population="
        f"{int(census_da_population['population_2021'].sum())}"
    )

    return census_da_population


def write_and_verify_layers(layers):
    if OUTPUT_GPKG.exists():
        OUTPUT_GPKG.unlink()

    for index, (layer_name, gdf) in enumerate(
        layers.items()
    ):
        mode = "w" if index == 0 else "a"
        gdf.to_file(
            OUTPUT_GPKG,
            layer=layer_name,
            driver="GPKG",
            engine="pyogrio",
            mode=mode,
        )
        print(
            f"Written {layer_name}: features={len(gdf)}"
        )

    written_layer_names = set(
        pyogrio.list_layers(OUTPUT_GPKG)[:, 0]
    )
    expected_layer_names = set(layers)

    if written_layer_names != expected_layer_names:
        raise ValueError(
            "GeoPackage layer mismatch: "
            f"expected={sorted(expected_layer_names)}, "
            f"actual={sorted(written_layer_names)}"
        )

    for layer_name, original in layers.items():
        loaded = gpd.read_file(
            OUTPUT_GPKG,
            layer=layer_name,
        )

        if len(loaded) != len(original):
            raise ValueError(
                f"{layer_name}: output feature count "
                "does not match input"
            )

        if loaded.crs.to_epsg() != 26910:
            raise ValueError(
                f"{layer_name}: output CRS is "
                f"{loaded.crs}, expected {TARGET_CRS}"
            )

        print(
            f"Verified {layer_name}: "
            f"features={len(loaded)}; crs={loaded.crs}"
        )


def main():
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Project root:", PROJECT_ROOT)
    print("Target CRS:", TARGET_CRS)
    print("Output:", OUTPUT_GPKG)

    parks = prepare_parks()
    roads = prepare_roads()
    municipal_boundary = (
        prepare_municipal_boundary()
    )
    census_da_population = (
        prepare_census_da_population(
            municipal_boundary
        )
    )

    layers = {
        "parks": parks,
        "roads": roads,
        "municipal_boundary": municipal_boundary,
        "census_da_population": (
            census_da_population
        ),
    }

    write_and_verify_layers(layers)


if __name__ == "__main__":
    main()
