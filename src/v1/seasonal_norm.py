"""Functions to calculate and retrieve seasonal norms for solar forecasts."""

import pandas as pd

# Typical solar capacity factor (performance metric for solar farms)
# This represents how much actual power is generated compared to theoretical maximum
TYPICAL_SOLAR_CAPACITY_FACTOR = 0.20

# Solar generation window (hours in UTC)
# Note: This is a simplified approximation and doesn't account for:
# - Different latitudes having very different daylight hours
# - Seasonal variation in sunrise/sunset times
# - Different longitudes within the same timezone
SOLAR_GENERATION_START_HOUR = 6
SOLAR_GENERATION_END_HOUR = 18


def get_simplified_seasonal_norm(
    forecast_df: pd.DataFrame,
    capacity: float,
    lat: float = 0.0,
) -> pd.DataFrame:
    """Calculate a simplified seasonal norm based on a solar generation model.

    This is a fast approximation that doesn't require API calls or historical data.
    It uses a simplified mathematical model based on:
    - Time of day (solar angle) - uses UTC time uniformly
    - Month (seasonal variation) - adjusts for hemisphere based on latitude
    - Solar capacity factor

    LIMITATIONS:
    - Uses UTC time uniformly, which may not match actual solar patterns
      for locations far from the prime meridian
    - Fixed generation window (6:00-18:00 UTC) doesn't account for
      latitude-dependent daylight hours or seasonal variation
    - Simplified model doesn't account for weather patterns or cloud cover

    Args:
        forecast_df: Forecast DataFrame with DatetimeIndex
        capacity: Solar capacity in GW
        lat: Latitude of the location (default 0.0). Used to adjust
             seasonal patterns for Southern Hemisphere (lat < 0)

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
    daily_pattern = np.where(
        (hour >= SOLAR_GENERATION_START_HOUR) & (hour <= SOLAR_GENERATION_END_HOUR),
        np.sin(np.pi * (hour - SOLAR_GENERATION_START_HOUR) / 12) ** 2,
        0.0,
    )

    # Seasonal variation
    # Northern Hemisphere: peak in summer (June/July), low in winter (Dec/Jan)
    # Southern Hemisphere: inverted pattern (peak in Dec/Jan)
    # Using a simple cosine model
    if lat >= 0:
        # Northern Hemisphere: peak at month 6.5 (late June/early July)
        seasonal_factor = 0.7 + 0.3 * np.cos(2 * np.pi * (month - 6.5) / 12)
    else:
        # Southern Hemisphere: peak at month 12.5 (late December/early January)
        seasonal_factor = 0.7 + 0.3 * np.cos(2 * np.pi * (month - 12.5) / 12)

    # Combine patterns and scale by capacity
    norm_power = daily_pattern * seasonal_factor * capacity * TYPICAL_SOLAR_CAPACITY_FACTOR

    result["power_gw_norm"] = norm_power

    return result
