"""Functions to calculate and retrieve seasonal norms for solar forecasts.

APPROACH:
=========
The seasonal norm is a physics-based mathematical model that estimates typical solar
power generation patterns WITHOUT requiring historical data or API calls.

CALCULATION METHOD:
==================
norm_power = daily_pattern * sun_intensity_factor * capacity * capacity_factor

Where:
1. daily_pattern: Sinusoidal curve representing sun position during the day
   - Uses solar declination to calculate actual sunrise/sunset times
   - Accounts for latitude (polar regions have extreme day lengths)
   - Adjusts for longitude (solar noon varies by location)

2. sun_intensity_factor: Solar radiation intensity based on sun elevation angle
   - Higher sun angle (summer/tropics) = more intense radiation
   - Lower sun angle (winter/poles) = less intense radiation
   - Based on actual solar declination angle for the month

3. capacity: Installed solar capacity in GW (from dataset)

4. capacity_factor: 0.20 (20%) - Typical solar farm performance accounting for:
   - Nighttime (no generation)
   - Weather/clouds
   - Panel efficiency losses
   - Temperature effects

PHYSICS CALCULATIONS:
====================
- Solar declination: 23.45° * sin(2π * (month - 3) / 12)
  * Varies from -23.45° (Dec 21) to +23.45° (Jun 21)
  * Determines seasonal sun position

- Day length: Uses sunrise equation from solar geometry
  * cos(hour_angle) = -tan(latitude) * tan(declination)
  * day_length = 2 * hour_angle / 15
  * Automatically handles extreme polar conditions

- Local solar time: UTC time adjusted by longitude
  * solar_hour = utc_hour + (longitude / 15)
  * Ensures solar noon (peak) occurs at correct local time

EXAMPLE OUTPUTS:
===============
Norway (60°N, 10°E) in June:
- Day length: ~19 hours
- Peak at 12:00 solar time (10:40 UTC)
- High sun angle = strong intensity

Norway in December:
- Day length: ~6 hours
- Peak at 12:00 solar time (10:40 UTC)
- Low sun angle = weak intensity

Australia (-25°S, 135°E) in December:
- Day length: ~14 hours
- Peak at 12:00 solar time (03:00 UTC)
- High sun angle (Southern summer)

ACCURACY:
=========
This is MORE accurate than the previous simple model because it:
+ Adjusts solar noon time for longitude (was fixed at 12:00 UTC)
+ Calculates actual day length based on latitude/season (was fixed 6-18)
+ Accounts for sun elevation angle affecting intensity
+ Handles polar regions correctly

LIMITATIONS:
===========
- Assumes clear sky (no weather/clouds)
- Doesn't account for terrain (mountains, shadows)
- Uses location centroid (countries span multiple time zones)
- Simplified atmospheric absorption model
"""

import pandas as pd

# Typical solar capacity factor (performance metric for solar farms)
# This represents how much actual power is generated compared to theoretical maximum
TYPICAL_SOLAR_CAPACITY_FACTOR = 0.20


def get_simplified_seasonal_norm(
    forecast_df: pd.DataFrame,
    capacity: float,
    lat: float = 0.0,
    lon: float = 0.0,
) -> pd.DataFrame:
    """Calculate a simplified seasonal norm based on a solar generation model.

    CALCULATION STEPS:
    1. Convert timestamp to UTC to ensure consistent time reference
    2. Calculate local solar time by adjusting UTC for longitude
    3. Determine solar declination angle based on month (season)
    4. Calculate sunrise/sunset times using solar geometry equations
    5. Generate daily power curve using sinusoidal pattern between sunrise/sunset
    6. Calculate sun elevation angle to determine radiation intensity
    7. Scale by capacity and typical capacity factor (20%)

    Args:
        forecast_df: Forecast DataFrame with DatetimeIndex (can be any timezone)
        capacity: Solar capacity in GW
        lat: Latitude in degrees (-90 to +90). Negative = Southern Hemisphere
        lon: Longitude in degrees (-180 to +180). Negative = West, Positive = East

    Returns:
        DataFrame with the same index and a 'power_gw_norm' column

    Example:
        For USA (38.5°N, -77°W) with 100 GW capacity in June at 17:00 UTC:
        - UTC hour: 17.0
        - Solar hour: 17.0 + (-77/15) = 17.0 - 5.13 = 11.87 (near solar noon)
        - Declination: +23.45° (summer)
        - Day length: ~15 hours (long summer day)
        - Sun elevation: high (strong radiation)
        - Result: ~19 GW (near peak generation)
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

    # STEP 2: Calculate local solar time by adjusting for longitude
    # Solar noon occurs when the sun is at the local meridian
    # Each 15° of longitude = 1 hour time difference
    # Example: New York (lon=-74°) has solar noon at 17:56 UTC (74/15 = 4.93 hours late)
    solar_hour = utc_hour + (lon / 15.0)
    solar_hour = solar_hour % 24  # Normalize to 0-24 range

    # STEP 3: Calculate solar declination angle (Earth's tilt effect)
    # Declination varies from -23.45° (Dec 21, winter solstice, NH winter)
    #                    to +23.45° (Jun 21, summer solstice, NH summer)
    # This determines how "high" the sun gets in the sky at different times of year
    declination = 23.45 * np.sin(2 * np.pi * (month - 3) / 12)

    # STEP 4: Calculate day length using sunrise equation from solar geometry
    # This accounts for latitude AND season
    # Formula: cos(hour_angle) = -tan(latitude) * tan(declination)
    lat_rad = np.radians(lat)
    decl_rad = np.radians(declination)

    cos_hour_angle = -np.tan(lat_rad) * np.tan(decl_rad)
    cos_hour_angle = np.clip(cos_hour_angle, -1, 1)  # Prevent math domain errors

    hour_angle = np.degrees(np.arccos(cos_hour_angle))
    day_length_hours = 2 * hour_angle / 15.0  # Convert angle to hours

    # Examples:
    # - Norway (60°N) in June: declination=+23°, day_length≈19 hours
    # - Norway (60°N) in Dec: declination=-23°, day_length≈6 hours
    # - Equator (0°) in any month: day_length≈12 hours

    sunrise_solar = 12 - day_length_hours / 2
    sunset_solar = 12 + day_length_hours / 2

    # STEP 5: Generate daily power curve (sinusoidal pattern)
    # Power follows sin²(x) curve between sunrise and sunset
    # This creates smooth bell curve peaking at solar noon (12:00 solar time)
    daily_pattern = np.where(
        (solar_hour >= sunrise_solar) & (solar_hour <= sunset_solar),
        np.sin(np.pi * (solar_hour - sunrise_solar) / day_length_hours) ** 2,
        0.0,
    )

    # STEP 6: Calculate sun elevation angle effect on radiation intensity
    # Higher sun in sky = more intense radiation (shorter path through atmosphere)
    # Maximum sun elevation at solar noon = 90° - |latitude - declination|
    max_sun_elevation = 90 - abs(lat - declination)

    # Examples:
    # - Oslo (60°N) in June: max_elev = 90 - |60-23| = 53° (moderate)
    # - Oslo (60°N) in Dec: max_elev = 90 - |60-(-23)| = 7° (very low, weak)
    # - Singapore (1°N) in June: max_elev = 90 - |1-23| = 68° (high)

    # Normalize to 0.3-1.0 range (minimum 30% intensity at very low angles)
    sun_intensity_factor = np.clip((max_sun_elevation - 23.45) / (90 - 23.45), 0.3, 1.0)

    # STEP 7: Final calculation combining all factors
    # Formula: power = daily_pattern * sun_intensity * capacity * capacity_factor
    # - daily_pattern: 0-1 (time of day effect, includes day length)
    # - sun_intensity_factor: 0.3-1.0 (sun elevation angle effect)
    # - capacity: installed GW
    # - capacity_factor: 0.20 (20% - accounts for weather, night, efficiency)
    norm_power = daily_pattern * sun_intensity_factor * capacity * TYPICAL_SOLAR_CAPACITY_FACTOR

    result["power_gw_norm"] = norm_power

    return result
