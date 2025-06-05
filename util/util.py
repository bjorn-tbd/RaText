import pandas as pd
import re
import json
import geopandas as gpd
from shapely.geometry import Point
import streamlit as st


def extract_concentration_data(entry: dict) -> pd.DataFrame:
    data = []
    pattern = re.compile(r'^(\d+)_')
    
    # Sort keys numerically by their prefix number
    sorted_items = sorted(
        ((int(pattern.match(k).group(1)), k, v) for k, v in entry.items() if pattern.match(k)),
        key=lambda x: x[0]
    )

    temp_block = {}
    block_count = 0
    strip_num = 1
    conc_labels = ["Control", "1x", "5x", "10x"]
    control_tic_seen = 0  # Tracks whether we're adding Alive or Dead

    for _, key, value in sorted_items:
        name = key.split("_", 1)[-1]

        if "Control_tic" in name:
            label = conc_labels[block_count % 4]
            if control_tic_seen % 2 == 0:
                temp_block[f"{label}_Alive"] = value
            else:
                temp_block[f"{label}_Dead"] = value
                block_count += 1  # Only increment block_count after completing both alive and dead
                if block_count % 4 == 0:
                    temp_block["Strip"] = f"Strip {strip_num}"
                    data.append(temp_block)
                    temp_block = {}
                    strip_num += 1
            control_tic_seen += 1

        elif "ticks_alive" in name:
            label = conc_labels[block_count % 4]
            temp_block[f"{label}_Alive"] = value

        elif "ticks_dead" in name:
            label = conc_labels[block_count % 4]
            temp_block[f"{label}_Dead"] = value
            block_count += 1
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

        # Find all concentrations from columns like "1x_Alive"
        concs = set()
        for col in df.columns:
            if col.endswith("_Alive"):
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
                    if (row[alive_col] + row[dead_col]) > 0 else None
                ),
                axis=1
            )

        new_mortality_data.append((box_id, df))
    
    return new_mortality_data


def append_region_to_box(data_tuples, geojson_path=r".\geojson_files\global.json"):
    import geopandas as gpd
    from shapely.geometry import Point
    import pandas as pd

    gdf_regions = gpd.read_file(geojson_path)
    records = []

    def is_resistant(alive, dead):
        total = alive + dead
        return (total > 0) and (alive / total > 0.25)

    for batch_name, df, loc in data_tuples:
        if loc is None:
            continue
        point = Point(loc["longitude"], loc["latitude"])

        for _, row in df.iterrows():
            try:
                r_1x = is_resistant(row["1x_Alive"], row["1x_Dead"])
                r_5x = is_resistant(row["5x_Alive"], row["5x_Dead"])
                r_10x = is_resistant(row["10x_Alive"], row["10x_Dead"])

                # Apply cascading: resistance at higher level means resistance at lower
                if r_10x:
                    r_5x = True
                    r_1x = True
                elif r_5x:
                    r_1x = True

            except KeyError:
                continue

            records.append({
                "geometry": point,
                "1x_resistant": r_1x,
                "5x_resistant": r_5x,
                "10x_resistant": r_10x
            })

    if not records:
        return None, None, None

    gdf_data = gpd.GeoDataFrame(records, crs="EPSG:4326")
    gdf_joined = gpd.sjoin(gdf_data, gdf_regions, how="inner", predicate="intersects")

    # Normalize region column name
    for possible in ["NAME_1", "NAME", "name"]:
        if possible in gdf_joined.columns:
            gdf_joined = gdf_joined.rename(columns={possible: "region"})
            break
    else:
        fallback = gdf_regions.columns[-1]
        gdf_joined = gdf_joined.rename(columns={fallback: "region"})

    # Group and calculate % of resistant strips per region
    grouped = gdf_joined.groupby("region").agg({
        "1x_resistant": "mean",
        "5x_resistant": "mean",
        "10x_resistant": "mean"
    }).reset_index()

    # Convert to %
    grouped["1x"] = grouped["1x_resistant"] * 100
    grouped["5x"] = grouped["5x_resistant"] * 100
    grouped["10x"] = grouped["10x_resistant"] * 100

    grouped = grouped[["region", "1x", "5x", "10x"]]

    return grouped, "region", gdf_regions