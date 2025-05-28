import streamlit as st
import pandas as pd
import requests
from util.util import extract_concentration_data
from util.visual_util import render_colored_table
import folium
from streamlit_folium import st_folium


API_URL = "https://five.epicollect.net/api/export/entries/ratext-academy?form_ref=216f96d4dddf431789397be865cc113d_6810df39b9ee1"


def main():
    st.title("Tick Mortality Viewer")

    try:
        # Assuming this returns the JSON structure as described
        batch_map, entries = get_data_from_thing()

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

        # --- Batch Selection ---
        st.subheader("Batch Details")
        if not batch_map:
            st.warning("No batch data found in the entries.")
            return

        selected_batch = st.selectbox("Select a batch number to view:", sorted(batch_map.keys()))
        selected_entry = batch_map[selected_batch]

        df = extract_concentration_data(selected_entry)
        render_colored_table(df)

    except Exception as e:
        st.error(f"Failed to load data from API: {e}")



def get_data_from_thing():
    response = requests.get(API_URL)
    json_data = response.json()
    entries = json_data["data"]["entries"]

    batch_map = {entry["3_batchnumber"]: entry for entry in entries if entry.get("3_batchnumber")}
    return batch_map, entries


if __name__ == "__main__":
    main()
