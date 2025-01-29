import streamlit as st
import folium
import openrouteservice
import requests
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static


def get_distance_and_route(client, coord1, coord2):
    try:
        route = client.directions(
            coordinates=[coord1, coord2],
            profile='driving-car',
            format='geojson'
        )
        distance_km = route['routes'][0]['summary']['distance'] / 1000
        return distance_km, route['routes'][0]['geometry']
    except Exception as e:
        st.error(f"Error fetching route: {e}")
        return None, None


def fetch_charging_stations():
    url = "https://api.openchargemap.io/v3/poi/"
    params = {
        "countrycode": "DE",
        "maxresults": 100,
        "compact": True,
        "verbose": False,
        "key": "a3bdd273-aa8d-4a18-bb43-6da37a564fbc"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return [(station["AddressInfo"]["Latitude"], station["AddressInfo"]["Longitude"]) for station in data]
    else:
        st.error("Failed to fetch charging station data.")
        return []


def plot_map(charging_stations, api_key):
    client = openrouteservice.Client(key=api_key)

    m = folium.Map(location=charging_stations[0], zoom_start=10)
    marker_cluster = MarkerCluster().add_to(m)

    for lat, lon in charging_stations:
        folium.Marker(location=[lat, lon], icon=folium.Icon(
            color='blue')).add_to(marker_cluster)

    for i in range(len(charging_stations) - 1):
        coord1 = charging_stations[i][::-1]
        coord2 = charging_stations[i + 1][::-1]

        distance, route_geometry = get_distance_and_route(
            client, coord1, coord2)
        if distance is not None and route_geometry:
            color = "green" if distance <= 50 else "red"
            folium.PolyLine(
                locations=[(p[1], p[0]) for p in openrouteservice.convert.decode_polyline(
                    route_geometry)['coordinates']],
                color=color,
                weight=5,
                opacity=0.7
            ).add_to(m)

    return m


st.title("EV Charging Stations Map (Germany Only)")

st.write("Fetching charging stations data online...")
charging_stations = fetch_charging_stations()

if charging_stations:
    api_key = st.text_input(
        "5b3ce3597851110001cf62485d6c7a3ba59c42bcbcbbda290dcea9fc", type="password")
    if api_key:
        charging_map = plot_map(charging_stations, api_key)
        folium_static(charging_map)
