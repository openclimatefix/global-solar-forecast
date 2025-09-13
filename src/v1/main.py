"""A Streamlit app to show global solar forecast."""
import json
import warnings
from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import pycountry
import streamlit as st
from country import country_page
from forecast import get_forecast

data_dir = "src/v1/data"


def main_page() -> None:
    """Main page, show a map of the world with the solar forecast."""
    st.header("Global Solar Forecast")

    # Lets load a map of the world
    world = gpd.read_file(f"{data_dir}/countries.geojson")

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
    global_solar_capacity = solar_capacity_per_country_df["capacity_gw"].sum()

    # drop down menu in side bar
    normalized = st.checkbox(
        "Normalised each countries solar forecast (0-100%)", value=False,
    )

    # run forecast for that countries
    forecast_per_country: dict[str, pd.DataFrame] = {}
    my_bar = st.progress(0)
    countries = list(pycountry.countries)
    for i in range(len(countries)):
        my_bar.progress(int(i/len(countries)*100),
                        f"Loading Solar forecast for {countries[i].name} \
                        ({countries[i].alpha_3}) \
                        ({i+1}/{len(countries)})")
        country = countries[i]

        if country.alpha_3 not in solar_capacity_per_country:
            continue

        country_map = world[world["adm0_a3"] == country.alpha_3]
        if country_map.empty:
            continue

        # get centroid of country
        # hide warning about GeoSeries.to_crs
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            centroid = country_map.geometry.to_crs(crs="EPSG:4326").centroid

        lat = centroid.y.values[0]
        lon = centroid.x.values[0]

        capacity = solar_capacity_per_country[country.alpha_3]
        forecast_data = get_forecast(country.name, capacity, lat, lon)

        if forecast_data is not None:
            forecast = pd.DataFrame(forecast_data)
            forecast = forecast.rename(columns={"power_kw": "power_gw"})

            # display normalized forecast
            if normalized:
                forecast["power_gw"] = forecast["power_gw"] / capacity * 100

            forecast_per_country[country.alpha_3] = forecast

    my_bar.progress(100, "Loaded all forecasts.")
    my_bar.empty()

    # format forecast into pandas dataframe with columns,
    # country code, timestamp, forecast_value
    all_forecasts: list[pd.DataFrame] = []
    for country_code, forecast in forecast_per_country.items():
        forecast["country_code"] = country_code
        all_forecasts.append(forecast)

    # concatenate all forecasts into a single dataframe
    all_forecasts_df = pd.concat(all_forecasts, ignore_index=False)
    all_forecasts_df.index.name = "timestamp"
    all_forecasts_df = all_forecasts_df.reset_index()

    # plot the total amount forecasted
    # group by country code and timestamp
    total_forecast = all_forecasts_df[["timestamp", "power_gw"]]
    total_forecast = total_forecast.groupby(["timestamp"]).sum().reset_index()

    # plot in ploty
    st.write(f"Global forecast, capacity of {global_solar_capacity} GW.")
    fig = go.Figure(data=go.Scatter(x=total_forecast["timestamp"],
                                    y=total_forecast["power_gw"],
                                    marker_color="#FF4901"))
    fig.update_layout(
        yaxis_title="Power [GW]",
        xaxis_title="Time (UTC)",
        yaxis_range=[0, None],
    )
    if not normalized:
        st.plotly_chart(fig)
    # now lets make a map plot, of the generation for different forecast
    # horizons
    # get available timestamps for the slider
    all_forecasts_df["timestamp"] = pd.to_datetime(all_forecasts_df["timestamp"])
    available_timestamps = sorted(all_forecasts_df["timestamp"].unique())
    # add slider to select forecast horizon
    st.subheader("Solar Forecast Map")
    st.write(
        "Use the slider below to view forecasts for different time horizons:",
    )

    # create slider with timestamp options
    if len(available_timestamps) > 0:
        # Calculate hours from now for better labels
        now = pd.Timestamp.utcnow().floor("h").replace(tzinfo=None)
        hours_ahead = [
            (ts - now).total_seconds() / 3600 for ts in available_timestamps
        ]

        # Create more descriptive slider labels
        def format_time_label(hours: float) -> str:
            if hours <= 0:
                return "Now"
            elif hours < 24:
                return f"+{int(hours)} hours"
            else:
                days = int(hours // 24)
                return f"+{days} day(s)"

        selected_timestamp_index = st.slider(
            "Select Forecast Time",
            min_value=0,
            max_value=len(available_timestamps) - 1,
            value=0,
            format="%d",
            help="Move slider to see forecasts at different times",
        )

        selected_timestamp = available_timestamps[selected_timestamp_index]
        hours_from_now = hours_ahead[selected_timestamp_index]
        time_label = format_time_label(hours_from_now)

        st.info(
            f"**Selected Time**: {time_label} | "
            f"{selected_timestamp.strftime('%Y-%m-%d %H:%M')} UTC",
        )

        # get generation for selected timestamp
        selected_generation = all_forecasts_df[
            all_forecasts_df["timestamp"] == selected_timestamp
        ]
        selected_generation = selected_generation[["country_code", "power_gw"]]
    else:
        st.error("No forecast data available for the map")
        return

    # join 'world' and 'selected_generation'
    world = world.merge(
        selected_generation,
        how="left",
        left_on="adm0_a3",
        right_on="country_code",
    )

    shapes_dict = json.loads(world.to_json())

    fig = go.Figure(data=go.Choroplethmap(
        geojson=shapes_dict,
        locations=world.index,
        z=world["power_gw"],
        colorscale="Viridis",
        colorbar_title="Power [GW]",
        marker_opacity=0.5,
        hovertemplate="<b>%{customdata}</b><br>Power: %{z:.2f} GW<extra></extra>",
        customdata=world["country_name"] if "country_name" in world.columns else world["adm0_a3"],
    ))

    fig.update_layout(
                mapbox_style="carto-positron",
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                geo_scope="world",
            )

    clicked_data = st.plotly_chart(fig, on_select="rerun", key="world_map")

    if clicked_data and clicked_data["selection"]["points"]:
        selected_point = clicked_data["selection"]["points"][0]
        clicked_country_index = selected_point["location"]

        if clicked_country_index < len(world):
            clicked_country_code = world.iloc[clicked_country_index]["adm0_a3"]

            if clicked_country_code in solar_capacity_per_country:
                st.session_state.selected_country_code = clicked_country_code
                st.switch_page(country_page_ref)
            else:
                st.warning("No forecast data available for the selected country")




def docs_page() -> None:
    """Documentation page."""
    st.markdown("# Documentation")
    st.write(
        "There are two main components to this app, the solar capacities "
        "and solar forecasts.",
    )

    st.markdown("## Solar Capacities")
    st.write(
        "Most of the solar capacities are taken from the "
        "[Ember](https://ember-energy.org/data/electricity-data-explorer/). "
        "This data is updated yearly and shows the total installed "
        "solar capacity "
        "per country in Gigawatts (GW). "
        "Some countries are missing from the Ember dataset, "
        "so we have manually added some countries from other sources.",
    )

    st.markdown("## Solar Forecasts")
    st.write(
        "The solar forecasts are taken from the "
        "[Quartz Open Solar API](https://open.quartz.solar/). "
        "The API provides solar forecasts for any location in the world, "
        "given the latitude, longitude and installed capacity. "
        "We use the centroid of each country as the location for the forecast",
    )

    st.markdown("## Caveats")
    st.write(
        "1. The solar capacities are yearly totals, "
        "so they do not account for new installations that year.",
    )
    st.write(
        "2. Some countries solar capacies are very well known, some are not.",
    )
    st.write(
        "3. The Quartz Open Solar API uses a ML model trained on UK "
        "domestic solar data. "
        "It's an unknown how well this model performs in other countries.",
    )
    st.write(
        "4. We use the centroid of each country as the location for "
        "the forecast, "
        "but the solar capacity may be concentrated in a different area "
        "of the country.",
    )
    st.write(
        "5. The forecast right now is quite spiky, "
        "we are looking into smoothing it out a bit.",
    )

    faqs = Path("./FAQ.md").read_text()
    st.markdown(faqs)


def capacities_page() -> None:
    """Solar capacities page."""
    st.header("Solar Capacities")
    st.write("This page shows the solar capacities per country.")
    solar_capacity_per_country_df = pd.read_csv(
        f"{data_dir}/solar_capacities.csv", index_col=0,
    )

    # remove nans in index
    solar_capacity_per_country_df["temp"] = solar_capacity_per_country_df.index
    solar_capacity_per_country_df.dropna(subset=["temp"], inplace=True)
    solar_capacity_per_country_df.drop(columns=["temp"], inplace=True)

    st.dataframe(solar_capacity_per_country_df)


if __name__ == "__main__":
    country_page_ref = st.Page(country_page, title="Country")

    pg = st.navigation([
        st.Page(main_page, title="Global", default=True),
        country_page_ref,
        st.Page(docs_page, title="About"),
        st.Page(capacities_page, title="Capacities"),
    ], position="top")
    pg.run()
