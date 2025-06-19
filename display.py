import streamlit as st
import pandas as pd
import requests
from util.util import extract_concentration_data, calculate_mortality_percentages, append_region_to_box
from util.visual_util import render_colored_table, show_resistance_charts, new_map
from util.api_util import get_data_from_thing
import folium
from streamlit_folium import st_folium
import json


st.set_page_config(layout="wide", page_icon="./resources/mini.png", page_title="DART Dashboard")
def main():
    st.title("**D**AR & **T**")
    st.markdown("**D**ashboard **A**caricide **R**esistance & **T**racking")

    try:
        # Assuming this returns the JSON structure as described
        batch_map, entries = get_data_from_thing()
        dashboarding(batch_map, entries)

    except Exception as e:
        st.error(f"Failed to load data from API: {e}")

    # st.warning("switching to local data for testing purposes.")
    # with open("./test3.json", "r") as f:
    #     json_data = json.load(f)
    # entries = json_data["data"]["entries"]
    # batch_map = {entry["16_batch_number"]: entry for entry in entries if entry.get("16_batch_number")}
    # dashboarding(batch_map, entries)


def dashboarding(batch_map, entries):

    # build location map from entries
    location_map = build_location_map(entries)
    # Extract batch data and calculate mortality
    RaT_boxnumbers = sorted(batch_map.keys())
    mortality_data = [
            (box, extract_concentration_data(batch_map[box])) for box in RaT_boxnumbers
        ]
    mortality_data = calculate_mortality_percentages(mortality_data)

        # Step 2: Append location data to mortality_data tuples
    mortality_data = [
            (box, mortality, location_map.get(box)) for (box, mortality) in mortality_data
        ]

    # Now each tuple looks like: (box, mortality_rate, {"latitude": ..., "longitude": ...})
    supported_countries = ["world", "ecuador", "uruguay"]  # TODO: more specific.
    region = st.selectbox("Select a region to view:", supported_countries)

    region_path = f"./geojson_files/{region}.json" if region != "world" else "./geojson_files/world.json"
    grouped, raw_coords = append_region_to_box(mortality_data, geojson_path=region_path)

    if grouped is not None:
        subregions = grouped["region"].dropna().unique().tolist()
        subregions.sort()

        selected_subregion = st.selectbox(f"Select a subregion in {region}:", subregions)
        filtered_grouped = grouped[grouped["region"] == selected_subregion]

        # NEW: Show resistance charts
        show_resistance_charts(filtered_grouped, "region")

        # Show the map with the selected subregion
        st.subheader(f"Map of {selected_subregion} with Batch Locations")
        new_map(raw_coords)
        
        # Keep your other logic
        with st.expander("Show Batch Details"):
            box_picker(batch_map)
    else:
        st.warning("No data available for the selected region.")


def build_location_map(entries):
    location_map = {}
    for entry in entries:
        box_name = entry.get("2_RaText_batch_numbe")  # Adjust key if needed
        loc = entry.get("3_Location_of_the_fa", {})
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        try:
            lat = float(lat)
            lon = float(lon)
            location_map[box_name] = {"latitude": lat, "longitude": lon}
        except (TypeError, ValueError):
            location_map[box_name] = None
    return location_map


def box_picker(batch_map):
    st.subheader("Batch Details")
    if not batch_map:
        st.warning("No batch data found in the entries.")
        return

    selected_box = st.selectbox("Select a batch number to view:", sorted(batch_map.keys()))
    ratext_box = batch_map[selected_box]

    df = extract_concentration_data(ratext_box) # for single box. 
    render_colored_table(df)


def column_1_map_n_logo(entries, col1):
    with col1:
        st.image("./resources/logo.png", use_container_width=True)
        st.subheader("Overview Map of Entries")

        # Extract valid coordinates
        coords = []
        for entry in entries:
            loc = entry.get("3_Location_of_the_fa", {}) #TODO: make this dynamic, so we can use it for other entries.
            lat = loc.get("latitude")
            lon = loc.get("longitude")

            try:
                lat = float(lat)
                lon = float(lon)
                coords.append({"latitude": lat, "longitude": lon})
            except (TypeError, ValueError):
                continue

        if coords:
            df = pd.DataFrame(coords)
            st.map(df)
        else:
            st.info("No valid location data available to display on the map.")


main()