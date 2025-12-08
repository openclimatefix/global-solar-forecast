"""Functions to calculate and retrieve seasonal norms for solar forecasts."""

import pandas as pd
import streamlit as st
from forecast import get_forecast

data_dir = "src/v1/data"


@st.cache_data(ttl="24h")
def calculate_seasonal_norm(
    country_name: str,
    capacity: float,
    lat: float,
    lon: float,
) -> pd.DataFrame | None:
    """Calculate seasonal norm for a country by averaging forecasts across a year.

    The seasonal norm depends on:
    - Time of day (hour)
    - Month
    - Country (via lat/lon and capacity)

    Args:
        country_name: Name of the country
        capacity: Solar capacity in GW
        lat: Latitude of the country centroid
        lon: Longitude of the country centroid

    Returns:
        DataFrame with columns: month, hour, power_gw_norm
        where month is 1-12 and hour is 0-23
    """
    if capacity == 0:
        return None

    # Generate timestamps for a full year, sampling every day
    # We'll use 2024 as a representative year (leap year for better coverage)
    year = 2024
    dates = pd.date_range(
        start=f"{year}-01-01",
        end=f"{year}-12-31",
        freq="D",
    )

    all_forecasts = []

    # For each day, get a forecast
    # To reduce API calls, we sample every 3 days instead of every day
    sample_dates = dates[::3]

    for _date in sample_dates:
        # Get forecast for this specific date
        forecast_data = get_forecast(country_name, capacity, lat, lon)

        if forecast_data is not None:
            forecast_df = pd.DataFrame(forecast_data)

            # Ensure we have power_kw column
            if "power_kw" not in forecast_df.columns:
                continue

            # Convert to GW (API returns kW)
            forecast_df["power_gw"] = forecast_df["power_kw"].astype(float)

            # Ensure timestamp index
            if "timestamp" in forecast_df.columns:
                forecast_df["timestamp"] = pd.to_datetime(forecast_df["timestamp"], utc=True)
                forecast_df = forecast_df.set_index("timestamp").sort_index()

            # Extract month and hour (ensure DatetimeIndex for type safety)
            if isinstance(forecast_df.index, pd.DatetimeIndex):
                forecast_df["month"] = forecast_df.index.month
                forecast_df["hour"] = forecast_df.index.hour

                all_forecasts.append(forecast_df[["month", "hour", "power_gw"]])

    if not all_forecasts:
        return None

    # Combine all forecasts
    combined = pd.concat(all_forecasts, ignore_index=False)

    # Calculate average for each (month, hour) combination
    seasonal_norm = combined.groupby(["month", "hour"])["power_gw"].mean().reset_index()
    seasonal_norm.rename(columns={"power_gw": "power_gw_norm"}, inplace=True)

    return seasonal_norm


@st.cache_data(ttl="24h")
def get_seasonal_norm_for_forecast(
    country_name: str,
    capacity: float,
    lat: float,
    lon: float,
    forecast_df: pd.DataFrame,
) -> pd.DataFrame:
    """Get seasonal norm values that match the timestamps in a forecast.

    Args:
        country_name: Name of the country
        capacity: Solar capacity in GW
        lat: Latitude of the country centroid
        lon: Longitude of the country centroid
        forecast_df: Current forecast DataFrame with DatetimeIndex

    Returns:
        DataFrame with the same index as forecast_df and a 'power_gw_norm' column
    """
    # Calculate seasonal norm
    seasonal_norm = calculate_seasonal_norm(country_name, capacity, lat, lon)

    if seasonal_norm is None:
        # Return zeros if we can't calculate norm
        result = pd.DataFrame(index=forecast_df.index)
        result["power_gw_norm"] = 0.0
        return result

    # Create result DataFrame with same index as forecast
    result = pd.DataFrame(index=forecast_df.index)

    # Extract month and hour from forecast index
    if not isinstance(result.index, pd.DatetimeIndex):
        result.index = pd.to_datetime(result.index)

    # Ensure timezone awareness
    if result.index.tz is None:
        result.index = result.index.tz_localize("UTC")

    # Convert to UTC for matching
    utc_index = result.index.tz_convert("UTC")

    result["month"] = utc_index.month
    result["hour"] = utc_index.hour

    # Merge with seasonal norm
    result = result.reset_index().merge(
        seasonal_norm,
        on=["month", "hour"],
        how="left",
    )

    # Fill any missing values with 0
    result["power_gw_norm"] = result["power_gw_norm"].fillna(0.0)

    # Set index back to timestamp
    result = result.set_index("index")
    result.index.name = None

    return result[["power_gw_norm"]]


def get_simplified_seasonal_norm(
    forecast_df: pd.DataFrame,
    capacity: float,
) -> pd.DataFrame:
    """Calculate a simplified seasonal norm based on a solar generation model.

    This is a fast approximation that doesn't require API calls.
    It uses a simple model based on:
    - Time of day (solar angle)
    - Month (seasonal variation)

    Args:
        forecast_df: Forecast DataFrame with DatetimeIndex
        capacity: Solar capacity in GW

    Returns:
        DataFrame with the same index and a 'power_gw_norm' column
    """
    import numpy as np

    result = pd.DataFrame(index=forecast_df.index)

    # Ensure datetime index
    if not isinstance(result.index, pd.DatetimeIndex):
        result.index = pd.to_datetime(result.index)

    # Work with UTC
    if result.index.tz is None:
        utc_index = result.index.tz_localize("UTC")
    else:
        utc_index = result.index.tz_convert("UTC")

    # Extract hour and month
    hour = utc_index.hour + utc_index.minute / 60.0
    month = utc_index.month

    # Simple solar generation model
    # Peak generation at solar noon (around 12:00 UTC, but varies by location)
    # Using a sinusoidal model for daily pattern
    # Assume generation between 6:00 and 18:00
    daily_pattern = np.where(
        (hour >= 6) & (hour <= 18),
        np.sin(np.pi * (hour - 6) / 12) ** 2,
        0.0,
    )

    # Seasonal variation: peak in summer (June/July), low in winter (Dec/Jan)
    # Using a simple cosine model with peak at month 6.5
    seasonal_factor = 0.7 + 0.3 * np.cos(2 * np.pi * (month - 6.5) / 12)

    # Combine patterns and scale by capacity
    # Typical capacity factor for solar is around 15-25%, we use 20%
    norm_power = daily_pattern * seasonal_factor * capacity * 0.20

    result["power_gw_norm"] = norm_power

    return result
