"""A Streamlit app to show global solar forecast."""
import warnings

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import pycountry
import streamlit as st
from forecast import get_forecast

data_dir = "src/v1/data"


def country_page() -> None:
    """Country page, select a country and see the forecast for that country."""
    st.header("Country Solar Forecast")
    st.write("This page will shows individual country forecasts")

    # Lets load a map of the world
    world = gpd.read_file(f"{data_dir}/countries.geojson")

    countries = list(pycountry.countries)

    # Get list of countries and their solar capcities now from the Ember API
    solar_capacity_per_country_df = pd.read_csv(
        f"{data_dir}/solar_capacities.csv", index_col=0,
    )

    # remove nans in index
    solar_capacity_per_country_df["temp"] = solar_capacity_per_country_df.index
    solar_capacity_per_country_df.dropna(subset=["temp"], inplace=True)

    # add column with country code and name
    solar_capacity_per_country_df["country_code_and_name"] = (
        solar_capacity_per_country_df.index + " - " +
        solar_capacity_per_country_df["country_name"]
    )

    # convert to dict
    solar_capacity_per_country = solar_capacity_per_country_df.to_dict()[
        "capacity_gw"
    ]
    country_code_and_names = list(
        solar_capacity_per_country_df["country_code_and_name"],
    )

    default_index = 0
    if "selected_country_code" in st.session_state:
        selected_code = st.session_state.selected_country_code
        for i, country_name in enumerate(country_code_and_names):
            if country_name.startswith(selected_code + " - "):
                default_index = i
                break
        # Clear the session state after using it
        del st.session_state.selected_country_code

    selected_country = st.selectbox(
        "Select a country:", country_code_and_names, index=default_index,
    )
    selected_country_code = selected_country.split(" - ")[0]

    country = next(c for c in countries if c.alpha_3 == selected_country_code)

    country_map = world[world["adm0_a3"] == country.alpha_3]

    # get centroid of country
    # hide warning about GeoSeries.to_crs
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        centroid = country_map.geometry.to_crs(crs="EPSG:4326").centroid

    lat = centroid.y.values[0]
    lon = centroid.x.values[0]

    capacity = solar_capacity_per_country[country.alpha_3]
    forecast_data = get_forecast(country.name, capacity, lat, lon)
    if forecast_data is None:
        st.error(f"Unable to get forecast for {country.name}")
        return
    forecast = pd.DataFrame(forecast_data)
    forecast = forecast.rename(columns={"power_kw": "power_gw"})

    # plot in ploty
    st.write(f"{country.name} Solar Forecast, capacity of {capacity} GW.")
    fig = go.Figure(data=go.Scatter(
        x=forecast.index,
        y=forecast["power_gw"],
        marker_color="#FF4901",
    ))
    fig.update_layout(
        yaxis_title="Power [GW]",
        xaxis_title="Time (UTC)",
        yaxis_range=[0, None],
    )

    st.plotly_chart(fig)


