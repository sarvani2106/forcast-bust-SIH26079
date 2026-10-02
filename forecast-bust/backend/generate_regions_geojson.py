"""
Generate backend/data/regions.geojson for SIH26079.

Creates real geographic boundaries for the regions used by the
SIH26079 Forecast Bust Detection project.

Sources:
1. India state GeoJSON:
   udit-001/india-maps-data

2. Andhra Pradesh district GeoJSON:
   satishvmadala/andhrapradesh_opendata_locations

Coastal Andhra is represented using the traditional coastal region:
Srikakulam, Vizianagaram, Visakhapatnam, East Godavari,
West Godavari, Krishna, Guntur, Prakasam and Nellore.

Run from the backend folder:

    python generate_regions_geojson.py

Output:

    backend/data/regions.geojson
"""

from pathlib import Path
import json
import requests

from shapely.geometry import shape, mapping
from shapely.ops import unary_union


# ============================================================
# DATA SOURCES
# ============================================================

STATE_SOURCE = (
    "https://cdn.jsdelivr.net/gh/"
    "udit-001/india-maps-data@main/"
    "geojson/states/{}.geojson"
)

AP_DISTRICTS_SOURCE = (
    "https://raw.githubusercontent.com/"
    "satishvmadala/andhrapradesh_opendata_locations/"
    "main/"
    "AndhraPradesh_Districts.geojson"
)


# ============================================================
# REGIONS USED BY SIH26079
# ============================================================

STATE_REGIONS = {
    "Karnataka": "karnataka",
    "Maharashtra": "maharashtra",
    "Odisha": "odisha",
    "Rajasthan": "rajasthan",
    "Tamil Nadu": "tamil-nadu",
    "Telangana": "telangana",
    "West Bengal": "west-bengal",
}


# ============================================================
# TRADITIONAL COASTAL ANDHRA DISTRICTS
# ============================================================

COASTAL_DISTRICTS = {
    "Srikakulam",
    "Vizianagaram",
    "Visakhapatnam",
    "East Godavari",
    "West Godavari",
    "Krishna",
    "Guntur",
    "Prakasam",
    "Nellore",
    "SPS Nellore",
    "Sri Potti Sriramulu Nellore",
}


# ============================================================
# DOWNLOAD JSON
# ============================================================

def get_json(url):
    print(f"Downloading: {url}")

    response = requests.get(
        url,
        timeout=60
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize(value):
    return (
        str(value)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace(".", "")
        .split()
    )


# ============================================================
# GET DISTRICT NAME FROM GEOJSON FEATURE
# ============================================================

def district_name(feature):

    properties = feature.get(
        "properties",
        {}
    )

    possible_keys = [
        "district",
        "DISTRICT",
        "District",
        "name",
        "NAME",
        "Name",
        "district_name",
        "District_Name",
        "DIST_NAME",
    ]

    for key in possible_keys:

        value = properties.get(key)

        if value:
            return str(value).strip()

    return ""


# ============================================================
# CHECK WHETHER DISTRICT IS COASTAL ANDHRA
# ============================================================

def is_coastal_district(name):

    normalized_name = " ".join(
        normalize(name)
    )

    for district in COASTAL_DISTRICTS:

        normalized_target = " ".join(
            normalize(district)
        )

        if normalized_name == normalized_target:
            return True

    return False


# ============================================================
# CREATE GEOJSON
# ============================================================

def main():

    # This script should be run from the project root.
    output = Path(
        "backend/data/regions.geojson"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    features = []


    # ========================================================
    # 1. ADD THE SEVEN STATE REGIONS
    # ========================================================

    print("\nCreating state regions...")

    for region_name, slug in STATE_REGIONS.items():

        data = get_json(
            STATE_SOURCE.format(slug)
        )

        source_features = data.get(
            "features",
            []
        )

        if not source_features:

            raise RuntimeError(
                f"No GeoJSON features found for {region_name}"
            )

        # Convert every polygon/multipolygon in the
        # state GeoJSON into Shapely geometry.
        geometries = []

        for source_feature in source_features:

            geometry = source_feature.get(
                "geometry"
            )

            if geometry:
                geom = shape(geometry)

                # Repair invalid geographic geometry
                # before merging.
                if not geom.is_valid:
                    geom = geom.buffer(0)

                if not geom.is_empty:
                    geometries.append(
                        geom
                    )

        if not geometries:

            raise RuntimeError(
                f"No valid geometry found for {region_name}"
            )

        # Merge all internal polygons into ONE state geometry.
        state_geometry = unary_union(
            geometries
        )

        state_feature = {

            "type": "Feature",

            "properties": {

                "name": region_name,

                "region_type": "state",

            },

            "geometry": mapping(
                state_geometry
            ),
        }

        features.append(
            state_feature
        )

        print(
            f"  ✓ {region_name}"
        )
    # ========================================================
    # 2. DOWNLOAD ANDHRA PRADESH DISTRICT DATA
    # ========================================================

    print(
        "\nDownloading Andhra Pradesh district boundaries..."
    )

    ap_data = get_json(
        AP_DISTRICTS_SOURCE
    )

    ap_features = ap_data.get(
        "features",
        []
    )

    if not ap_features:

        raise RuntimeError(
            "No Andhra Pradesh district features found."
        )


    # ========================================================
    # 3. SELECT TRADITIONAL COASTAL ANDHRA DISTRICTS
    # ========================================================

    coastal_features = []

    print(
        "\nFinding traditional Coastal Andhra districts..."
    )

    for feature in ap_features:

        name = district_name(
            feature
        )

        if is_coastal_district(name):

            coastal_features.append(
                feature
            )

            print(
                f"  ✓ {name}"
            )


    if not coastal_features:

        raise RuntimeError(
            "No Coastal Andhra districts were matched."
        )


    # ========================================================
    # 4. DISSOLVE DISTRICTS INTO ONE COASTAL ANDHRA REGION
    # ========================================================

    print(
        "\nCombining Coastal Andhra districts..."
    )

    geometries = []

    for feature in coastal_features:

        geometry = feature.get(
            "geometry"
        )

        if geometry:

            geometries.append(
                shape(geometry)
            )


    if not geometries:

        raise RuntimeError(
            "Coastal Andhra districts have no geometry."
        )


    coastal_geometry = unary_union(
        geometries
    )


    # ========================================================
    # 5. CREATE COASTAL ANDHRA FEATURE
    # ========================================================

    coastal_feature = {

        "type": "Feature",

        "properties": {

            "name": "Coastal Andhra",

            "region_type": "traditional_region",

            "source_regions": [
                district_name(feature)
                for feature in coastal_features
            ],
        },

        "geometry": mapping(
            coastal_geometry
        ),
    }


    # Put Coastal Andhra first.
    features.insert(
        0,
        coastal_feature
    )


    # ========================================================
    # 6. CREATE FINAL FEATURE COLLECTION
    # ========================================================

    geojson = {

        "type": "FeatureCollection",

        "name": "SIH26079 Forecast Risk Regions",

        "features": features,
    }


    # ========================================================
    # 7. WRITE FILE
    # ========================================================

    output.write_text(
        json.dumps(
            geojson,
            ensure_ascii=False,
            separators=(
                ",",
                ":"
            ),
        ),
        encoding="utf-8"
    )


    # ========================================================
    # 8. VALIDATION OUTPUT
    # ========================================================

    print(
        "\n======================================"
    )

    print(
        "GeoJSON created successfully!"
    )

    print(
        "======================================"
    )

    print(
        f"\nFile: {output}"
    )

    print(
        f"Total regions: {len(features)}"
    )

    print(
        "\nRegions:"
    )

    for feature in features:

        print(
            f"  ✓ {feature['properties']['name']}"
        )


if __name__ == "__main__":

    main()