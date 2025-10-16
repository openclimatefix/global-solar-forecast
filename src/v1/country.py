"""A Streamlit app to show global solar forecast."""

from zoneinfo import ZoneInfo

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import pycountry
import pytz
import streamlit as st
from forecast import get_forecast

data_dir = "src/v1/data"

# Pre-load world geometries once
WORLD = gpd.read_file(f"{data_dir}/countries.geojson").to_crs(crs="EPSG:4326")

# Pre-compute centroids for all countries
WORLD_PROJECTED = WORLD.to_crs("EPSG:3857")  # or EPSG:6933 for equal-area
CENTROIDS = (
    WORLD_PROJECTED.set_index("adm0_a3")
    .geometry.centroid
    .to_crs("EPSG:4326")
    .to_frame(name="geometry")
)
CENTROIDS["lat"] = CENTROIDS.geometry.y
CENTROIDS["lon"] = CENTROIDS.geometry.x


def get_country_timezone(country_name: str) -> str:
    """Get timezone for a country based on its name using pycountry and pytz."""
    # Handle regional/organizational groupings that aren't countries
    non_countries = {
        "Africa",
        "ASEAN",
        "Asia",
        "EU",
        "Europe",
        "G20",
        "G7",
        "Latin America and Caribbean",
        "Middle East",
        "North America",
        "Oceania",
        "OECD",
        "World",
    }
    if country_name in non_countries:
        return "UTC"

    try:
        name_mappings = {
            "United States of America": "United States",
            "Russian Federation (the)": "Russian Federation",
            "Philippines (the)": "Philippines",
            "Dominican Republic (the)": "Dominican Republic",
            "Iran (Islamic Republic of)": "Iran",
            "Czechia": "Czech Republic",
            "Bosnia Herzegovina": "Bosnia and Herzegovina",
            "Viet Nam": "Vietnam",
            "Dem. Rep. Congo": "Congo, The Democratic Republic of the",
        }

        lookup_name = name_mappings.get(country_name, country_name)
        country = pycountry.countries.lookup(lookup_name)

        country_timezones = pytz.country_timezones.get(country.alpha_2, [])

        if country_timezones:
            preferred_timezones = {
                "US": "America/New_York",  # Eastern Time (most populated)
                "RU": "Europe/Moscow",  # Moscow Time
                "AU": "Australia/Sydney",  # Eastern Australia
                "BR": "America/Sao_Paulo",  # Brasília Time (most populated)
                "CA": "America/Toronto",  # Eastern Canada
                "MX": "America/Mexico_City",  # Central Mexico
                "AR": "America/Argentina/Buenos_Aires",  # Argentina
                "CL": "America/Santiago",  # Chile
                "KZ": "Asia/Almaty",  # Kazakhstan
                "MN": "Asia/Ulaanbaatar",  # Mongolia
                "CD": "Africa/Kinshasa",  # DRC
                "ID": "Asia/Jakarta",  # Indonesia
            }

            return preferred_timezones.get(country.alpha_2, country_timezones[0])
        else:
            return "UTC"

    except (LookupError, AttributeError):
        return "UTC"


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


def get_country_coords(country_code: str) -> tuple[float, float]:
    """Return lat, lon for a given ISO alpha-3 code."""
    if country_code in CENTROIDS.index:
        row = CENTROIDS.loc[country_code]
        return float(row["lat"]), float(row["lon"])

    # Fallback manual coordinates for very small states not in geojson
    fallback_coords = {
        "HKG": (22.3193, 114.1694),
        "SGP": (1.3521, 103.8198),
        "MAC": (22.1987, 113.5439),
        "MDV": (3.2028, 73.2207),
        "AND": (42.5462, 1.6016),
        "LUX": (49.6117, 6.1319),
        "MCO": (43.7384, 7.4246),
        "SMR": (43.9336, 12.4508),
        "VAT": (41.9029, 12.4534),
        "NRU": (-0.5228, 166.9315),
        "TUV": (-7.1095, 177.6493),
        "KIR": (1.8709, 157.3630),
        "PLW": (7.5149, 134.5825),
        "WSM": (-13.7590, -172.1046),
        # Newly added missing countries / territories
        "ATG": (17.0608, -61.7964),  # Antigua and Barbuda
        "BHS": (25.0343, -77.3963),  # Bahamas
        "BRB": (13.1939, -59.5432),  # Barbados
        "BLZ": (17.1899, -88.4976),  # Belize
        "DMA": (15.4150, -61.3710),  # Dominica
        "GRD": (12.1165, -61.6790),  # Grenada
        "KNA": (17.3578, -62.7830),  # Saint Kitts and Nevis
        "LCA": (13.9094, -60.9789),  # Saint Lucia
        "VCT": (13.2528, -61.1971),  # Saint Vincent and the Grenadines
        "SYC": (-4.6796, 55.4920),   # Seychelles
        "COM": (-11.6455, 43.3333),  # Comoros
        "STP": (0.1864, 6.6131),     # São Tomé and Príncipe
        "TLS": (-8.8742, 125.7275),  # Timor-Leste
        "FJI": (-17.7134, 178.0650), # Fiji
        "TON": (-21.1789, -175.1982),# Tonga
        "VUT": (-15.3767, 166.9592), # Vanuatu
        "SLB": (-9.6457, 160.1562),  # Solomon Islands
        "MHL": (7.1315, 171.1845),   # Marshall Islands
        "FSM": (6.8878, 158.2150),   # Micronesia
        "CPV": (14.9177, -23.5090),  # Cabo Verde
        "BRN": (4.5353, 114.7277),   # Brunei
        "BHR": (26.0667, 50.5577),   # Bahrain
        "DJI": (11.8251, 42.5903),   # Djibouti
        "GNB": (11.8037, -15.1804),  # Guinea-Bissau
        "SWZ": (-26.5225, 31.4659),  # Eswatini
        "LSO": (-29.6099, 28.2336),  # Lesotho
        "ATA": (-82.8628, 135.0000), # Antarctica
        "ATF": (-49.2800, 69.3500),  # French Southern and Antarctic Lands
        "FLK": (-51.7963, -59.5236), # Falkland Islands
        "GRL": (71.7069, -42.6043),  # Greenland
        "NCL": (-21.5511, 165.6180), # New Caledonia
        "COK": (-21.2367, -159.7777), # Cook Islands
        "NIU": (-19.0544, -169.8672), # Niue
        "PYF": (-17.6797, -149.4068), # French Polynesia
        "ASM": (-14.2706, -170.1322), # American Samoa
        "GUM": (13.4443, 144.7937),  # Guam
        "TKL": (-9.2002, -171.8480), # Tokelau
        "MLT": (35.9375, 14.3754),  # Malta
        "ESH" : (24.2155, -12.8858),  # Western Sahara
    }
    return fallback_coords.get(country_code, (0, 0))


def country_page() -> None:
    """Country page, select a country and see the forecast for that country."""
    st.header("Country Solar Forecast")
    st.write("This page shows individual country forecasts in local time")

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

    # Robust coordinate lookup
    lat, lon = get_country_coords(country.alpha_3)

    # Get timezone for this country using robust country-name approach
    timezone_str = get_country_timezone(country.name)
    st.info(f"Displaying forecast in {country.name} local time (Timezone: {timezone_str})")

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
        ),
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
