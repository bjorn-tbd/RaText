import streamlit as st
import requests
import json


# Set up API constants
API_URL = "https://five.epicollect.net/api/export/entries/ratext-academy?form_ref=216f96d4dddf431789397be865cc113d_6810df39b9ee1"
API_TOKEN = "hcZ3P1KhuOvTmC7MvqnMj38LNF0xGtyjJQXEzZ01" # what is data safety?
CLIENT_ID = 6427
CLIENT_SECRET = "KIdLBg0ZCLLRLpmbXMuYeddvJ1VUBAAdRLcs26VX"

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

    batch_map = {entry["2_RaText_batch_numbe"]: entry for entry in entries if entry.get("2_RaText_batch_numbe")}
    return batch_map, entries
