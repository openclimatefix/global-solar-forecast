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
    lon: float = 0.0,
) -> pd.DataFrame:
    """Calculate a simplified seasonal norm based on a solar generation model.

    This is a fast approximation that doesn't require API calls or historical data.
    It uses a simplified mathematical model based on:
    - Time of day (solar angle) - adjusted for longitude to get local solar time
    - Month (seasonal variation) - adjusts for hemisphere based on latitude
    - Solar capacity factor

    LIMITATIONS:
    - Fixed generation window doesn't account for latitude-dependent daylight hours
    - Simplified model doesn't account for weather patterns or cloud cover
    - Uses simplified day length (doesn't vary by season)

    Args:
        forecast_df: Forecast DataFrame with DatetimeIndex
        capacity: Solar capacity in GW
        lat: Latitude of the location (default 0.0). Used to adjust
             seasonal patterns for Southern Hemisphere (lat < 0)
        lon: Longitude of the location (default 0.0). Used to adjust
             solar noon time for the location

    Returns:
        DataFrame with the same index and a 'power_gw_norm' column
    """
    import numpy as np

    result = pd.DataFrame(index=forecast_df.index)

    # Ensure datetime index
    if not isinstance(result.index, pd.DatetimeIndex):
        result.index = pd.to_datetime(result.index)

    # Work with UTC first to calculate solar time
    if result.index.tz is None:
        utc_index = result.index.tz_localize("UTC")
    else:
        utc_index = result.index.tz_convert("UTC")

    # Extract hour and month from UTC
    utc_hour = utc_index.hour + utc_index.minute / 60.0
    month = utc_index.month

    # Calculate local solar time by adjusting for longitude
    # Solar noon occurs when the sun is at the local meridian
    # Longitude adjustment: each 15° of longitude = 1 hour time difference
    # Positive longitude (East) means earlier solar noon in UTC
    # Negative longitude (West) means later solar noon in UTC
    solar_hour = utc_hour + (lon / 15.0)
    # Normalize to 0-24 range
    solar_hour = solar_hour % 24

    # Calculate day length based on latitude and month
    # More accurate model accounting for seasonal variation in daylight
    # Using simplified declination: -23.45° at winter solstice, +23.45° at summer
    declination = 23.45 * np.sin(2 * np.pi * (month - 3) / 12)

    # Hour angle at sunrise/sunset using the sunrise equation
    # cos(hour_angle) = -tan(lat) * tan(declination)
    lat_rad = np.radians(lat)
    decl_rad = np.radians(declination)

    # Handle polar day/night cases
    cos_hour_angle = -np.tan(lat_rad) * np.tan(decl_rad)
    cos_hour_angle = np.clip(cos_hour_angle, -1, 1)  # Prevent math errors

    hour_angle = np.degrees(np.arccos(cos_hour_angle))
    day_length_hours = 2 * hour_angle / 15.0  # Convert to hours

    # Calculate sunrise and sunset in solar time
    sunrise_solar = 12 - day_length_hours / 2
    sunset_solar = 12 + day_length_hours / 2

    # Simple solar generation model using actual day length
    # Peak generation at solar noon (12:00 solar time)
    # Using a sinusoidal model for daily pattern
    daily_pattern = np.where(
        (solar_hour >= sunrise_solar) & (solar_hour <= sunset_solar),
        np.sin(np.pi * (solar_hour - sunrise_solar) / day_length_hours) ** 2,
        0.0,
    )

    # Seasonal variation based on solar declination
    # Northern Hemisphere: peak in summer (June/July), low in winter (Dec/Jan)
    # Southern Hemisphere: inverted pattern (peak in Dec/Jan)
    # Using actual solar declination gives us the seasonal strength

    # The seasonal factor should account for:
    # 1. Day length (already in daily_pattern via day_length_hours)
    # 2. Sun angle/intensity (higher sun = more power per hour)

    # Sun elevation factor: higher sun angle = more intense radiation
    # Maximum sun elevation = 90° - |lat - declination|
    max_sun_elevation = 90 - abs(lat - declination)
    # Normalize to 0-1 range (assuming minimum useful elevation is 23.45°)
    sun_intensity_factor = np.clip((max_sun_elevation - 23.45) / (90 - 23.45), 0.3, 1.0)

    # Combine patterns and scale by capacity
    norm_power = daily_pattern * sun_intensity_factor * capacity * TYPICAL_SOLAR_CAPACITY_FACTOR

    result["power_gw_norm"] = norm_power

    return result
