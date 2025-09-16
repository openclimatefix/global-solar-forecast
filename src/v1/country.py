"""A Streamlit app to show global solar forecast."""

import warnings
from pathlib import Path
from zoneinfo import ZoneInfo

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import pycountry
import streamlit as st
from forecast import get_forecast
from timezonefinder import TimezoneFinder

data_dir = "src/v1/data"


def display_ocf_logo() -> None:
    """Display OCF logo as an elegant header banner."""
    logo_path = "src/assets/ocf_logo.png"

    # Add custom CSS for better styling
    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 1rem;
        }

        /* Custom styling for the app */
        .stApp {
            background-color: var(--background-color);
        }

        /* Header styling */
        .ocf-header {
            background: linear-gradient(135deg, #DC143C 0%, #B22222 30%, #CD5C5C 70%, #F08080 100%);
            padding: 18px 0;
            margin: -1rem -1rem 2rem -1rem;
            border-radius: 0 0 12px 12px;
            box-shadow: 0 3px 10px rgba(220, 20, 60, 0.12);
            border-bottom: 2px solid rgba(220, 20, 60, 0.2);
        }

        .ocf-header:hover {
            box-shadow: 0 5px 16px rgba(220, 20, 60, 0.18);
            transform: translateY(-1px);
            transition: all 0.3s ease;
        }

        /* Logo and text container */
        .ocf-content {
            display: flex;
            align-items: center;
            justify-content: center;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        .ocf-link {
            display: flex;
            align-items: center;
            text-decoration: none;
            color: white;
            transition: transform 0.2s ease;
        }

        .ocf-link:hover {
            transform: scale(1.03);
        }

        .ocf-link:hover .ocf-text {
            text-shadow: 0 3px 8px rgba(0,0,0,0.3);
            transform: translateY(-1px);
        }

        .ocf-logo {
            height: 40px;
            width: auto;
            margin-right: 15px;
            filter: brightness(0) invert(1);
            drop-shadow: 0 2px 6px rgba(0,0,0,0.3);
        }

        .ocf-text {
            font-family: 'Source Code Pro', 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-weight: 600;
            font-size: 20px;
            letter-spacing: 0.5px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            color: #ffffff;
            text-transform: none;
            line-height: 1.3;
            margin-top: 2px;
        }

        /* Responsive design */
        @media (max-width: 768px) {
            .ocf-text {
                font-size: 18px;
                letter-spacing: 0.3px;
            }
            .ocf-logo {
                height: 35px;
                margin-right: 12px;
            }
        }

        @media (max-width: 480px) {
            .ocf-text {
                font-size: 16px;
                letter-spacing: 0.2px;
            }
            .ocf-logo {
                height: 32px;
                margin-right: 10px;
            }
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Check if logo file exists
    if Path(logo_path).exists():
        # Create a header banner with OCF branding
        st.markdown(
            f"""
            <div class="ocf-header">
                <div class="ocf-content">
                    <a href="https://openclimatefix.org" target="_blank" class="ocf-link">
                        <img src="data:image/png;base64,{_get_base64_encoded_image(logo_path)}"
                             class="ocf-logo"
                             alt="Open Climate Fix Logo">
                        <div class="ocf-text">
                            Open Climate Fix
                        </div>
                    </a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _get_base64_encoded_image(image_path: str) -> str:
    """Convert image to base64 string for embedding in HTML."""
    import base64

    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def get_country_timezone(lat: float, lon: float) -> str:
    """Get timezone for a country based on its coordinates."""
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=lat, lng=lon)
    return timezone_str or "UTC"


def convert_utc_to_local_time(forecast_df: pd.DataFrame, timezone_str: str) -> pd.DataFrame:
    """Convert UTC timestamps to local time for a given timezone."""
    forecast_df = forecast_df.copy()

    # Convert index to datetime if it's not already
    if not isinstance(forecast_df.index, pd.DatetimeIndex):
        forecast_df.index = pd.to_datetime(forecast_df.index)

    # Ensure index is UTC
    if forecast_df.index.tz is None:
        forecast_df.index = forecast_df.index.tz_localize("UTC")

    # Convert to local timezone
    try:
        local_tz = ZoneInfo(timezone_str)
        forecast_df.index = forecast_df.index.tz_convert(local_tz)
    except Exception:
        # If timezone conversion fails, keep as UTC
        st.warning(f"Could not convert to timezone {timezone_str}, using UTC")

    return forecast_df


def country_page() -> None:
    """Country page, select a country and see the forecast for that country."""
    # Display OCF logo in sidebar
    display_ocf_logo()

    st.header("Country Solar Forecast")
    st.write("This page shows individual country forecasts in local time")

    # Lets load a map of the world
    world = gpd.read_file(f"{data_dir}/countries.geojson")

    countries = list(pycountry.countries)

    # Get list of countries and their solar capcities now from the Ember API
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
        "Select a country:",
        country_code_and_names,
        index=default_index,
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

    # Get timezone for this country using robust country-name approach
    timezone_str = get_country_timezone(lat, lon)
    st.info(f" Displaying forecast in {country.name} local time (Timezone: {timezone_str})")

    capacity = solar_capacity_per_country[country.alpha_3]
    forecast_data = get_forecast(country.name, capacity, lat, lon)

    if forecast_data is None:
        st.error(f"Unable to get forecast for {country.name}")
        return

    forecast = pd.DataFrame(forecast_data)
    forecast = forecast.rename(columns={"power_kw": "power_gw"})

    # Convert timestamps to local time
    forecast = convert_utc_to_local_time(forecast, timezone_str)

    # plot in ploty
    st.write(f"{country.name} Solar Forecast, capacity of {capacity} GW.")
    fig = go.Figure(
        data=go.Scatter(
            x=forecast.index,
            y=forecast["power_gw"],
            marker_color="#FF4901",
        )
    )
    fig.update_layout(
        yaxis_title="Power [GW]",
        xaxis_title="Local Time",
        yaxis_range=[0, None],
        title=f"Solar Forecast for {country.name} (Local Time)",
    )

    st.plotly_chart(fig)

    # Show forecast data table with local time
    with st.expander("View Forecast Data"):
        st.dataframe(forecast)
