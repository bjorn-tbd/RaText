import streamlit as st
import pandas as pd
import requests
from util.util import extract_concentration_data, calculate_mortality_percentages
from util.visual_util import render_colored_table, draw_mortality_donut, show_mortality_charts
import folium
from streamlit_folium import st_folium


API_URL = "https://five.epicollect.net/api/export/entries/ratext-academy?form_ref=216f96d4dddf431789397be865cc113d_6810df39b9ee1"
API_TOKEN = "216f96d4dddf431789397be865cc113d_6810df39b9ee1" # what is data safety?


st.set_page_config(layout="wide")
def main():
    st.title("**D**AR & **T**")
    st.markdown("**D**ashboard **A**carice **R**esistance & **T**racking")

    try:
        # Assuming this returns the JSON structure as described
        batch_map, entries = get_data_from_thing()


        col1, col2 = st.columns([1, 3])

        column_1_map_n_logo(entries, col1)

        with col2:
            #todo: extract acarice data earlier than currently, so we can use it for the circle diagrams. 
            RaT_boxnumbers = sorted(batch_map.keys())
            mortality_data = [
                (box, extract_concentration_data(batch_map[box])) for box in RaT_boxnumbers
            ]
            mortality_data = calculate_mortality_percentages(mortality_data)


            show_mortality_charts(mortality_data)
            box_picker(batch_map)

            print("done")

    except Exception as e:
        st.error(f"Failed to load data from API: {e}")

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
        st.image("./resources/logo.png")
        # --- Overview Map Component ---
        st.subheader("Overview Map of Entries")

        map_center = [0.0, 0.0]  # Default center; can adjust based on data
        overview_map = folium.Map(location=map_center, zoom_start=2)

        has_location = False
        for entry in entries:
            loc = entry.get("4_location", {})
            lat, lon = loc.get("latitude"), loc.get("longitude")

            try:
                lat = float(lat)
                lon = float(lon)
                has_location = True

                folium.Marker(
                        location=[lat, lon],
                        popup=f"Batch: {entry['3_batchnumber']}\nName: {entry['2_name']}",
                        tooltip=entry['3_batchnumber']
                    ).add_to(overview_map)

            except (TypeError, ValueError):
                continue  # Skip entries with invalid coordinates

        if has_location:
            st_folium(overview_map, width=700)
        else:
            st.info("No valid location data available to display on the map.")


@st.cache_data(ttl=450)  # Cache for 450 seconds
def get_data_from_thing():
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }

    response = requests.get(API_URL, headers=headers)
    response.raise_for_status()  # Raises an error if the response status is not 200
    json_data = response.json()
    entries = json_data["data"]["entries"]

    batch_map = {entry["3_batchnumber"]: entry for entry in entries if entry.get("3_batchnumber")}
    return batch_map, entries