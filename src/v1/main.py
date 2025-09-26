"""A Streamlit app to show global solar forecast."""

import json
import warnings
from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import pycountry
import streamlit as st
from constants import ocf_palette
from country import country_page
from forecast import get_forecast

data_dir = "src/v1/data"


def main_page() -> None:
    """Main page, show a map of the world with the solar forecast."""
    # Add title with logo beside it
    cols = st.columns([0.85, 0.15])
    with cols[0]:
        st.header("Global Solar Forecast")
    with cols[1]:
        logo_path = "src/assets/ocf_logo_dark_square.png"
        if Path(logo_path).exists():
            st.markdown(
                f'<a href="https://www.openclimatefix.org" target="_blank">'
                f'<img src="data:image/png;base64,{get_image_base64(logo_path)}" '
                f'style="width: 100%; height: auto; display: block;" />'
                f"</a>",
                unsafe_allow_html=True,
            )

    st.write(
        "This application provides a global forecast of solar power generation "
        "for then next 48 hours. "
        "We have modelled each countries solar generation seperately, "
        "using [open quartz solar](https://open.quartz.solar/docs), "
        "which uses live weather data.",
    )

    # Lets load a map of the world
    world = gpd.read_file(f"{data_dir}/countries.geojson")

    # Get list of countries and their solar capacities now from the Ember API
    solar_capacity_per_country_df = pd.read_csv(
        f"{data_dir}/solar_capacities.csv",
        index_col=0,
    )

    # remove nans in index
    solar_capacity_per_country_df["temp"] = solar_capacity_per_country_df.index
    solar_capacity_per_country_df.dropna(subset=["temp"], inplace=True)

    # add column with country code and name
    solar_capacity_per_country_df["country_code_and_name"] = (
        solar_capacity_per_country_df.index + " - " + solar_capacity_per_country_df["country_name"]
    )

    # convert to dict
    solar_capacity_per_country = solar_capacity_per_country_df.to_dict()["capacity_gw"]
    global_solar_capacity = solar_capacity_per_country_df["capacity_gw"].sum()

    # run forecast for each country
    forecast_per_country: dict[str, pd.DataFrame] = {}
    my_bar = st.progress(0)
    countries = list(pycountry.countries)
    for i in range(len(countries)):
        my_bar.progress(
            int(i / len(countries) * 100),
            f"Loading Solar forecast for {countries[i].name} "
            f"({countries[i].alpha_3}) "
            f"({i + 1}/{len(countries)})",
        )
        country = countries[i]

        if country.alpha_3 not in solar_capacity_per_country:
            continue

        country_map = world[world["adm0_a3"] == country.alpha_3]
        if country_map.empty:
            continue

        # get centroid of country
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            centroid = country_map.geometry.to_crs(crs="EPSG:4326").centroid

        lat = centroid.y.values[0]
        lon = centroid.x.values[0]

        capacity = solar_capacity_per_country[country.alpha_3]
        if capacity == 0.0:
            continue
        forecast_data = get_forecast(country.name, capacity, lat, lon)

        if forecast_data is not None:
            forecast = pd.DataFrame(forecast_data)
            # Ensure timestamp column is parsed and timezone-aware (UTC)
            if "timestamp" in forecast.columns:
                forecast["timestamp"] = pd.to_datetime(forecast["timestamp"], utc=True)
                forecast = forecast.set_index("timestamp").sort_index()

            # Convert units explicitly: API returns kW (power_kw) -> convert to GW
            if "power_kw" in forecast.columns:
                # No scaling needed since capacity is in GW and API returns kW
                forecast["power_gw"] = forecast["power_kw"].astype(float)
            elif "power_gw" not in forecast.columns:
                # unexpected format; skip this country
                continue

            if capacity == 0.0:
                forecast["power_percentage"] = None
            else:
                forecast["power_percentage"] = forecast["power_gw"] / float(capacity) * 100

            forecast_per_country[country.alpha_3] = forecast

    my_bar.progress(100, "Loaded all forecasts.")
    my_bar.empty()

    # format forecast into pandas dataframe
    all_forecasts: list[pd.DataFrame] = []
    for country_code, forecast in forecast_per_country.items():
        forecast["country_code"] = country_code
        all_forecasts.append(forecast)

    all_forecasts_df = pd.concat(all_forecasts, ignore_index=False)
    all_forecasts_df.index.name = "timestamp"
    all_forecasts_df = all_forecasts_df.reset_index()

    # plot the total amount forecasted and stacked chart option
    total_forecast = all_forecasts_df[["timestamp", "power_gw"]]
    total_forecast = total_forecast.groupby(["timestamp"]).sum().reset_index()

    st.write(
        f"Total global solar capacity is {global_solar_capacity:.2f} GW. "
        "Of course this number is always changing so please see the `Capacities` tab "
        "for actual the numbers we have used. ",
    )
    # Toggle to show stacked chart (top N countries + Other)
    show_stacked = st.checkbox("Show stacked global chart (top 20 countries)", value=False)

    if not show_stacked:
        fig = go.Figure(
            data=go.Scatter(
                x=total_forecast["timestamp"],
                y=total_forecast["power_gw"],
                marker_color="#FF4901",
            ),
        )
        fig.update_layout(
            yaxis_title="Power [GW]",
            xaxis_title="Time (UTC)",
            yaxis_range=[0, None],
            title="Global Solar Power Forecast",
        )
        st.plotly_chart(fig)
    else:
        # Prepare stacked data: pivot per country
        pivot = all_forecasts_df.pivot_table(
            index="timestamp",
            columns="country_code",
            values="power_gw",
            aggfunc="sum",
        ).fillna(0)

        # pick top N countries by peak contribution
        top_n = 20
        country_sums = pivot.sum().sort_values(ascending=False)
        top_countries = list(country_sums.head(top_n).index)
        other_countries = [c for c in pivot.columns if c not in top_countries]

        stacked_df = pivot[top_countries].copy()
        if other_countries:
            stacked_df["Other"] = pivot[other_countries].sum(axis=1)

        fig = go.Figure()
        cols = list(stacked_df.columns)  # type: ignore[arg-type]
        for i, col in enumerate(cols):
            color = ocf_palette[i % len(ocf_palette)]
            fig.add_trace(
                go.Scatter(
                    x=stacked_df.index,
                    y=stacked_df[col],
                    mode="lines",
                    name=col,
                    stackgroup="one",
                    line={"width": 0.5, "color": color},
                ),
            )

        fig.update_layout(
            yaxis_title="Power [GW]",
            xaxis_title="Time (UTC)",
            yaxis_range=[0, None],
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        )
        st.plotly_chart(fig)

    # forecast map
    all_forecasts_df["timestamp"] = pd.to_datetime(all_forecasts_df["timestamp"])
    available_timestamps = sorted(all_forecasts_df["timestamp"].unique())

    st.subheader("Solar Forecast Map")
    st.write("Use the slider below to view forecasts for different time horizons:")

    if len(available_timestamps) > 0:
        now = pd.Timestamp.utcnow().floor("h").replace(tzinfo=None)
        hours_ahead = [(ts - now).total_seconds() / 3600 for ts in available_timestamps]

        def format_time_label(hours: float) -> str:
            if hours <= 0:
                return "Now"
            elif hours < 24:
                return f"+{int(hours)} hours"
            else:
                days = int(hours // 24)
                return f"+{days} day(s)"

        selected_hours = st.slider(
            "Select Forecast Time (hours from now)",
            min_value=0.0,
            max_value=max(hours_ahead),
            value=0.0,
            step=0.25,
            format="%.1f h",
            help="Move slider to see forecasts at different times",
        )

        # Find the closest timestamp index to the selected hours
        selected_timestamp_index = min(
            range(len(hours_ahead)),
            key=lambda i: abs(hours_ahead[i] - selected_hours),
        )

        selected_timestamp = available_timestamps[selected_timestamp_index]
        hours_from_now = hours_ahead[selected_timestamp_index]
        time_label = format_time_label(hours_from_now)

        st.info(
            f"**Selected Time**: {time_label} | "
            f"{selected_timestamp.strftime('%Y-%m-%d %H:%M')} UTC",
        )

        selected_generation = all_forecasts_df[all_forecasts_df["timestamp"] == selected_timestamp]
        selected_generation = selected_generation[["country_code", "power_gw", "power_percentage"]]
    else:
        st.error("No forecast data available for the map")
        return

    normalized = st.checkbox(
        "Normalised each countries solar forecast (0-100%)",
        value=False,
    )

    world = world.merge(
        selected_generation,
        how="left",
        left_on="adm0_a3",
        right_on="country_code",
    )

    shapes_dict = json.loads(world.to_json())

    fig = go.Figure(
        data=go.Choroplethmap(
            geojson=shapes_dict,
            locations=world.index,
            z=world["power_percentage" if normalized else "power_gw"],
            colorscale="Viridis",
            colorbar_title="Power [%]" if normalized else "Power [GW]",
            marker_opacity=0.5,
            hovertemplate="<b>%{customdata}</b><br>Power: %{z:.2f} GW<extra></extra>",
            customdata=world["country_name"]
            if "country_name" in world.columns
            else world["adm0_a3"],
        ),
    )

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


def get_image_base64(image_path: str) -> str:
    """Convert image to base64 string for embedding in HTML."""
    import base64

    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def docs_page() -> None:
    """Documentation page."""
    st.markdown("# Documentation")
    st.write("There are two main components to this app, the solar capacities and solar forecasts.")

    st.markdown("## Solar Capacities")
    st.write(
        "Most of the solar capacities are taken from the "
        "[Ember](https://ember-energy.org/data/electricity-data-explorer/). "
        "This data is updated yearly and shows the total installed solar capacity "
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
        "1. The solar capacities are yearly totals, so they do not account for new installations.",
    )
    st.write("2. Some countries solar capacities are very well known, some are not.")
    st.write("3. The Quartz Open Solar API uses a ML model trained on UK solar data.")
    st.write("4. We use the centroid of each country as the forecast location.")
    st.write("5. The forecast right now is quite spiky; we are looking into smoothing it.")

    faqs = Path("./FAQ.md").read_text()
    st.markdown(faqs)


def capacities_page() -> None:
    """Solar capacities page."""
    st.header("Solar Capacities")
    st.write("This page shows the solar capacities per country.")
    solar_capacity_per_country_df = pd.read_csv(
        f"{data_dir}/solar_capacities.csv",
        index_col=0,
    )
    solar_capacity_per_country_df["temp"] = solar_capacity_per_country_df.index
    solar_capacity_per_country_df.dropna(subset=["temp"], inplace=True)
    solar_capacity_per_country_df.drop(columns=["temp"], inplace=True)

    st.dataframe(solar_capacity_per_country_df)


if __name__ == "__main__":
    # Compact header styling
    st.markdown(
        """
        <style>
            [data-testid="stHeader"] {
                height: 60px !important;
                min-height: 60px !important;
                padding: 0 1rem !important;
                border-bottom: 1px solid rgba(0,0,0,0.1);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    country_page_ref = st.Page(country_page, title="Country")

    pg = st.navigation(
        [
            st.Page(main_page, title="Global", default=True),
            country_page_ref,
            st.Page(capacities_page, title="Capacities"),
            st.Page(docs_page, title="About"),
        ],
        position="top",
    )
    pg.run()
