import streamlit as st
import pandas as pd
import requests
from util.util import extract_concentration_data, calculate_mortality_percentages, append_region_to_box
from util.visual_util import render_colored_table, show_mortality_charts
import folium
from streamlit_folium import st_folium
import json


API_URL = "https://five.epicollect.net/api/export/entries/ratext-academy?form_ref=216f96d4dddf431789397be865cc113d_6810df39b9ee1"
API_TOKEN = "hcZ3P1KhuOvTmC7MvqnMj38LNF0xGtyjJQXEzZ01" # what is data safety?
CLIENT_ID = 6427
CLIENT_SECRET = "KIdLBg0ZCLLRLpmbXMuYeddvJ1VUBAAdRLcs26VX"

st.set_page_config(layout="wide", page_icon="./resources/mini.png", page_title="DART Dashboard")
def main():
    st.title("**D**AR & **T**")
    st.markdown("**D**ashboard **A**carice **R**esistance & **T**racking")

    # try:
    #     # Assuming this returns the JSON structure as described
    #     batch_map, entries = get_data_from_thing()
    #     dashboarding(batch_map, entries)

    # except Exception as e:
    #     st.error(f"Failed to load data from API: {e}")

    st.warning("switching to local data for testing purposes.")
    with open("./test.json", "r") as f:
        json_data = json.load(f)
    entries = json_data["data"]["entries"]
    batch_map = {entry["16_batch_number"]: entry for entry in entries if entry.get("16_batch_number")}
    dashboarding(batch_map, entries)


def dashboarding(batch_map, entries):
    col1, col2 = st.columns([1, 3])

        # build location map from entries
    location_map = build_location_map(entries)

        # Show logo and map, TOOD: ensure location map is used here, instead of inner calc.
    column_1_map_n_logo(entries, col1)

    with col2:
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
        supported_countries = ["world", "ecuador"] # TODO: more
        region = st.selectbox("Select a region to view:", supported_countries)
        region_path = "./geojson_files/world.json"
        if region != "world":
            region_path = f"./geojson_files/{region}.json"

        grouped, region_column, gdf_regions = append_region_to_box(mortality_data, geojson_path=region_path)

        show_mortality_charts(grouped, region_column)
        box_picker(batch_map)


def build_location_map(entries):
    location_map = {}
    for entry in entries:
        box_name = entry.get("16_batch_number")  # Adjust key if needed
        loc = entry.get("17_location", {})
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
        st.image("./resources/logo.png")
        st.subheader("Overview Map of Entries")

        # Extract valid coordinates
        coords = []
        for entry in entries:
            loc = entry.get("17_location", {}) #TODO: make this dynamic, so we can use it for other entries.
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


@st.cache_data(ttl=1800)  # Cache for 1800 seconds
def get_epicollect_token(client_id, client_secret):
    url = "https://five.epicollect.net/api/oauth/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers = {
        "Content-Type": "application/vnd.api+json"
    }

    response = requests.post(url, headers=headers, data=json.dumps(params))

    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token"), token_data.get("expires_in")
    else:
        raise Exception(f"Failed to retrieve token: {response.status_code} {response.text}")


# Updated data fetching function with Authorization header
@st.cache_data(ttl=1800)  # Cache for 1800 seconds (30 minutes)
def get_data_from_thing(api_url=API_URL,client_id = CLIENT_ID ,client_secret= CLIENT_SECRET):
    # Get the OAuth token first
    access_token, expires_in = get_epicollect_token(client_id, client_secret)
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Use the token in the GET request
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()  # Raises an error if the response status is not 200

    json_data = response.json() # json response now broken, fix later.


    entries = json_data["data"]["entries"]

    batch_map = {entry["16_batch_number"]: entry for entry in entries if entry.get("16_batch_number")}
    return batch_map, entries

main()