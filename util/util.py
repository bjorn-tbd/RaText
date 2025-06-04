import pandas as pd
import re
import json
import geopandas as gpd
from shapely.geometry import Point
import streamlit as st


def extract_concentration_data(entry: dict) -> pd.DataFrame:
    data = []
    # Extract all relevant keys and sort by numeric prefix
    pattern = re.compile(r'^(\d+)_')
    sorted_items = sorted(
        ((int(pattern.match(k).group(1)), k, v) for k, v in entry.items() if pattern.match(k)),
        key=lambda x: x[0]
    )

    # Initialize row data
    row = {}
    strip_num = 1
    block_count = 0  # Each strip has 4 blocks: Control, 1x, 5x, 10x
    conc_labels = ["Control", "1x", "5x", "10x"]

    # Temporarily store values to identify grouping
    temp_block = {}

    for _, key, value in sorted_items:
        name = key.split("_", 1)[-1]

        if "Control_tic" in name:
            label = conc_labels[block_count % 4]
            if f"{label}_Alive" not in temp_block:
                temp_block[f"{label}_Alive"] = value
            else:
                temp_block[f"{label}_Dead"] = value

        elif "ticks_alive" in name:
            label = conc_labels[block_count % 4]
            temp_block[f"{label}_Alive"] = value

        elif "ticks_dead" in name:
            label = conc_labels[block_count % 4]
            temp_block[f"{label}_Dead"] = value
            block_count += 1

            # After every 4 blocks, we complete a strip
            if block_count % 4 == 0:
                temp_block["Strip"] = f"Strip {strip_num}"
                data.append(temp_block)
                temp_block = {}
                strip_num += 1

    return pd.DataFrame(data)


def calculate_mortality_percentages(mortality_data: list[tuple[str, pd.DataFrame]]) -> list[tuple[str, pd.DataFrame]]:
    """
    Calculate mortality percentages for each concentration in the DataFrame.

    Args:
        mortality_data (list): List of (box_id, DataFrame) tuples containing alive and dead counts.

    Returns:
        list: Updated list with mortality percentages added to each DataFrame.
    """
    new_mortality_data = []


    for box_id, df in mortality_data:
        df = df.copy()

        # Automatically find concentration labels (e.g., "1x", "5x", "10x")
        concs = set()
        for col in df.columns:
            if "_Alive" in col:
                conc = col.replace("_Alive", "")
                if f"{conc}_Dead" in df.columns:
                    concs.add(conc)

        for conc in sorted(concs):  # consistent order
            alive_col = f"{conc}_Alive"
            dead_col = f"{conc}_Dead"
            mortality_col = f"{conc}_Mortality (%)"

            df[mortality_col] = df.apply(
                lambda row: (
                    (row[dead_col] / (row[alive_col] + row[dead_col]) * 100)
                    if (row.get(alive_col, 0) + row.get(dead_col, 0)) > 0 else 0.0
                ),
                axis=1
            )

        new_mortality_data.append((box_id, df))
    return new_mortality_data



def append_region_to_box(data_tuples, geojson_path=r".\geojson_files\global.json"):
    gdf_regions = gpd.read_file(geojson_path)  # Load regions only once

    # Create a DataFrame from all data_tuples
    records = []
    for batch_name, df, loc in data_tuples:
        if loc is None:
            continue
        point = Point(loc["longitude"], loc["latitude"])
        for _, row in df.iterrows():
            records.append({
                "geometry": point,
                "1x": row["1x_Mortality (%)"],
                "5x": row["5x_Mortality (%)"],
                "10x": row["10x_Mortality (%)"]
            })

    if not records:
        return None, None, None

    gdf_data = gpd.GeoDataFrame(records, crs="EPSG:4326")

    # Spatial join: match points to regions
    gdf_joined = gpd.sjoin(gdf_data, gdf_regions, how="inner", predicate="intersects")



    # TODO: fix this part, the fkin geojson_path is not working
    # st.write(geojson_path)
    # Determine the region column to use for grouping
    if "NAME_1" in gdf_joined.columns:
        region_column = "NAME_1"
        unified_region_column = "region"
        gdf_joined = gdf_joined.rename(columns={"NAME_1": unified_region_column})
    elif "NAME" in gdf_joined.columns:
        region_column = "NAME"
        unified_region_column = "region"
        gdf_joined = gdf_joined.rename(columns={"NAME": unified_region_column})
    elif "name" in gdf_joined.columns:
        region_column = "name"
        unified_region_column = "region"
        gdf_joined = gdf_joined.rename(columns={"name": unified_region_column})
    else:
        # fallback to last column
        region_column = gdf_regions.columns[-1]
        unified_region_column = "region"
        gdf_joined = gdf_joined.rename(columns={region_column: unified_region_column})

    grouped = gdf_joined.groupby(unified_region_column).agg({
        "1x": "mean",
        "5x": "mean",
        "10x": "mean"
    }).reset_index()

    return grouped, unified_region_column, gdf_regions