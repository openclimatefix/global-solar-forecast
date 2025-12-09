"""Calculate seasonal norms from historical forecast data.

This module computes seasonal norms by averaging forecasts over multiple years.
The approach takes historical data for each country and calculates monthly averages
to establish baseline patterns. These norms automatically scale with capacity changes.
"""

import logging

import pandas as pd
import streamlit as st
from forecast import get_forecast

logger = logging.getLogger(__name__)


@st.cache_data(ttl="720h")  # Cache for 30 days
def calculate_seasonal_norm_from_forecasts(
    country_name: str,
    capacity: float,
    lat: float,
    lon: float,
    years: int = 3,
    samples_per_month: int = 2,
) -> pd.DataFrame | None:
    """Calculate seasonal norm by averaging multiple historical forecasts.

    Args:
        country_name: Country name
        capacity: Solar capacity in GW
        lat: Latitude
        lon: Longitude
        years: Years to average over (default 3)
        samples_per_month: Samples per month (default 2)

    Returns:
        DataFrame with columns: month, hour, power_gw_norm
    """
    if capacity == 0:
        return None

    all_forecasts = []

    # Sample across years and months
    for _ in range(years):
        for _month in range(1, 13):
            for sample in range(samples_per_month):
                # Spread samples throughout month
                day = 1 + (sample * 14)
                if day > 28:
                    day = 28

                try:
                    # Get forecast
                    forecast_data = get_forecast(country_name, capacity, lat, lon)

                    if forecast_data is not None:
                        forecast_df = pd.DataFrame(forecast_data)

                        if "power_kw" in forecast_df.columns:
                            forecast_df["power_gw"] = forecast_df["power_kw"] / 1_000_000

                            if "timestamp" in forecast_df.columns:
                                forecast_df["timestamp"] = pd.to_datetime(
                                    forecast_df["timestamp"],
                                    utc=True,
                                )
                                forecast_df = forecast_df.set_index("timestamp").sort_index()

                            if isinstance(forecast_df.index, pd.DatetimeIndex):
                                forecast_df["month"] = forecast_df.index.month
                                forecast_df["hour"] = forecast_df.index.hour
                                all_forecasts.append(
                                    forecast_df[["month", "hour", "power_gw"]],
                                )
                except Exception as e:
                    logger.debug("Failed to get forecast for %s: %s", country_name, e)
                    continue

    if not all_forecasts:
        return None

    # Average by month and hour
    combined = pd.concat(all_forecasts, ignore_index=False)
    seasonal_norm = (
        combined.groupby(["month", "hour"])["power_gw"]
        .mean()
        .reset_index()
        .rename(columns={"power_gw": "power_gw_norm"})
    )

    return seasonal_norm


def get_seasonal_norm_for_forecast(
    country_name: str,
    capacity: float,
    lat: float,
    lon: float,
    forecast_df: pd.DataFrame,
) -> pd.DataFrame:
    """Match seasonal norm to forecast timestamps.

    Args:
        country_name: Country name
        capacity: Solar capacity in GW
        lat: Latitude
        lon: Longitude
        forecast_df: Current forecast with DatetimeIndex

    Returns:
        DataFrame with same index and 'power_gw_norm' column
    """
    seasonal_norm = calculate_seasonal_norm_from_forecasts(
        country_name,
        capacity,
        lat,
        lon,
    )

    if seasonal_norm is None:
        result = pd.DataFrame(index=forecast_df.index)
        result["power_gw_norm"] = 0.0
        return result

    # Match by month and hour
    result = pd.DataFrame(index=forecast_df.index)

    if not isinstance(result.index, pd.DatetimeIndex):
        result.index = pd.to_datetime(result.index)

    if result.index.tz is None:
        utc_index = result.index.tz_localize("UTC")
    else:
        utc_index = result.index.tz_convert("UTC")

    result["month"] = utc_index.month
    result["hour"] = utc_index.hour

    # Merge with seasonal norm
    result = result.reset_index().merge(
        seasonal_norm,
        on=["month", "hour"],
        how="left",
    )

    result["power_gw_norm"] = result["power_gw_norm"].fillna(0.0)
    result = result.set_index("index")
    result.index.name = None

    return result[["power_gw_norm"]]


def aggregate_seasonal_norms_for_countries(
    forecast_per_country: dict[str, pd.DataFrame],
    solar_capacity_per_country: dict[str, float],
    country_coords: dict[str, tuple[float, float]],
    country_names: dict[str, str],
) -> pd.DataFrame:
    """Calculate and aggregate seasonal norms for all countries.

    Args:
        forecast_per_country: Dict of country_code -> forecast DataFrame
        solar_capacity_per_country: Dict of country_code -> capacity GW
        country_coords: Dict of country_code -> (lat, lon)
        country_names: Dict of country_code -> country name

    Returns:
        DataFrame with timestamp index and total seasonal norm
    """
    all_norms = []

    for country_code, forecast_df in forecast_per_country.items():
        capacity = solar_capacity_per_country.get(country_code, 0)
        if capacity == 0:
            continue

        coords = country_coords.get(country_code)
        if coords is None:
            continue

        lat, lon = coords
        country_name = country_names.get(country_code, country_code)

        # Get seasonal norm for this country
        norm_df = get_seasonal_norm_for_forecast(
            country_name,
            capacity,
            lat,
            lon,
            forecast_df,
        )

        if not norm_df.empty:
            all_norms.append(norm_df)

    if not all_norms:
        return pd.DataFrame()

    # Sum all country norms
    total_norm = pd.concat(all_norms, axis=1).sum(axis=1)
    result = pd.DataFrame({"power_gw_norm": total_norm})

    return result
