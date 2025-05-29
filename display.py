import streamlit as st
import pandas as pd
import requests
from util.util import extract_concentration_data, calculate_mortality_percentages
from util.visual_util import render_colored_table, draw_mortality_donut, show_mortality_charts
import folium
from streamlit_folium import st_folium
import json


API_URL = "https://five.epicollect.net/api/export/entries/ratext-academy?form_ref=216f96d4dddf431789397be865cc113d_6810df39b9ee1"
API_TOKEN = "hcZ3P1KhuOvTmC7MvqnMj38LNF0xGtyjJQXEzZ01" # what is data safety?

# API_URL = "https://five.epicollect.net/api/export/project/ratext-academy"  # Replace with your actual data endpoint
CLIENT_ID = 6427
CLIENT_SECRET = "KIdLBg0ZCLLRLpmbXMuYeddvJ1VUBAAdRLcs26VX"


st.set_page_config(layout="wide")
def main():
    st.title("**D**AR & **T**")
    st.markdown("**D**ashboard **A**carice **R**esistance & **T**racking")

    try:
        # Assuming this returns the JSON structure as described
        batch_map, entries = get_data_from_thing()

        print(entries)


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


# @st.cache_data(ttl=450)  # Cache for 450 seconds
# Your existing token function
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

    batch_map = {entry["3_batchnumber"]: entry for entry in entries if entry.get("3_batchnumber")}
    return batch_map, entries

main()