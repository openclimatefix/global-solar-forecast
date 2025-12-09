# Seasonal Norm Calculation - Technical Explanation

## Overview
The seasonal norm is a **simplified mathematical model** that estimates typical solar power generation patterns. It does NOT use historical data or API calls - it's a pure mathematical approximation.

## The Formula

```
norm_power = daily_pattern × seasonal_factor × capacity × capacity_factor
```

Where each component is:

### 1. Daily Pattern (Intraday Solar Curve)
```python
daily_pattern = sin²(π × (hour - 6) / 12)  for hours between 6:00-18:00 UTC
              = 0                           for hours outside 6:00-18:00 UTC
```

**What this does:**
- Creates a smooth bell curve peaking at noon (12:00 UTC)
- `sin²` produces values from 0 to 1
- Hour 6 → sin²(0) = 0 (sunrise)
- Hour 12 → sin²(π/2) = 1 (solar noon, maximum)
- Hour 18 → sin²(π) = 0 (sunset)

**Example values:**
- 6:00 UTC: 0.00 (no generation)
- 9:00 UTC: 0.50 (25% of max, because sin²(π/4) = 0.5)
- 12:00 UTC: 1.00 (100% of max)
- 15:00 UTC: 0.50 (25% of max)
- 18:00 UTC: 0.00 (no generation)

### 2. Seasonal Factor (Annual Variation)

**Northern Hemisphere (lat ≥ 0):**
```python
seasonal_factor = 0.7 + 0.3 × cos(2π × (month - 6.5) / 12)
```

**Southern Hemisphere (lat < 0):**
```python
seasonal_factor = 0.7 + 0.3 × cos(2π × (month - 12.5) / 12)
```

**What this does:**
- Varies between 0.7 (winter) and 1.0 (summer)
- 30% seasonal variation amplitude
- Northern Hemisphere peaks in June/July
- Southern Hemisphere peaks in December/January

**Northern Hemisphere Example values:**
- January (month 1): 0.7 + 0.3 × cos(2π × -5.5/12) ≈ 0.775 (winter, low)
- June (month 6): 0.7 + 0.3 × cos(2π × -0.5/12) ≈ 0.996 (summer, high)
- July (month 7): 0.7 + 0.3 × cos(2π × 0.5/12) ≈ 0.996 (summer, high)
- December (month 12): 0.7 + 0.3 × cos(2π × 5.5/12) ≈ 0.775 (winter, low)

### 3. Capacity Factor
```python
TYPICAL_SOLAR_CAPACITY_FACTOR = 0.20
```

**What this represents:**
- Solar panels operate at ~15-25% of their nameplate capacity on average
- Accounts for:
  - Night time (no generation)
  - Weather (clouds, rain)
  - Panel efficiency
  - Temperature effects
  - Dust/soiling
- We use 20% as a typical global average

### 4. Capacity
The installed solar capacity in GW (from the dataset)

## Complete Example Calculation

**For USA (lat = 38.5°N) in June at 12:00 UTC with 100 GW capacity:**

1. **Daily pattern:** 
   - Hour = 12
   - sin²(π × (12 - 6) / 12) = sin²(π/2) = 1.0

2. **Seasonal factor (Northern Hemisphere):**
   - Month = 6
   - 0.7 + 0.3 × cos(2π × (6 - 6.5) / 12)
   - = 0.7 + 0.3 × cos(-0.0833π)
   - = 0.7 + 0.3 × 0.997
   - ≈ 0.999 (peak summer)

3. **Capacity factor:** 0.20

4. **Final calculation:**
   - norm_power = 1.0 × 0.999 × 100 × 0.20
   - **≈ 19.98 GW**

**For USA in December at 12:00 UTC with 100 GW capacity:**

1. **Daily pattern:** 1.0 (same, solar noon)

2. **Seasonal factor:**
   - Month = 12
   - 0.7 + 0.3 × cos(2π × (12 - 6.5) / 12)
   - = 0.7 + 0.3 × cos(0.917π)
   - = 0.7 + 0.3 × 0.259
   - ≈ 0.778 (winter minimum)

3. **Final calculation:**
   - norm_power = 1.0 × 0.778 × 100 × 0.20
   - **≈ 15.56 GW**

## Key Limitations (Why It Might Look "Wrong")

### 1. **Uses UTC Time Uniformly**
- A country at longitude -75° (e.g., Eastern USA) has solar noon around 17:00 UTC, not 12:00 UTC
- The model assumes solar noon at 12:00 UTC for everyone
- This causes the daily peak to be shifted by (longitude/15) hours off

### 2. **Fixed 12-Hour Day Length**
- Assumes 6:00-18:00 generation window for everyone
- Reality: 
  - Nordic countries: 18+ hours of daylight in summer, 4 hours in winter
  - Equatorial countries: ~12 hours year-round
  - This makes high-latitude seasonal variation look too flat

### 3. **Only 30% Seasonal Variation**
- Real seasonal variation at high latitudes can be 80%+
- At equator, it's nearly flat
- We use a global average of 30%

### 4. **No Weather/Geography**
- Doesn't account for monsoons, rainy seasons
- Doesn't account for local climate patterns
- Treats desert and cloudy regions the same

## Why These Values Were Chosen

- **Capacity Factor (20%)**: Based on global average solar capacity factors from IRENA data
- **Seasonal Range (0.7-1.0)**: Represents typical ~30% seasonal variation in temperate regions
- **Daily Pattern (sin²)**: Standard solar irradiance model that matches observed bell curve
- **6:00-18:00 window**: Simplified 12-hour day approximation

## Recommendations for Improvement

To make the seasonal norm more accurate, we could:

1. **Add longitude adjustment:**
   ```python
   solar_noon_utc = 12 - (longitude / 15)
   ```

2. **Add latitude-dependent day length:**
   ```python
   day_length = calculate_day_length(lat, month)
   ```

3. **Use latitude-dependent seasonal amplitude:**
   ```python
   seasonal_amplitude = 0.1 + 0.7 * abs(lat) / 90  # More variation at poles
   ```

4. **Adjust capacity factor by latitude:**
   ```python
   capacity_factor = 0.25 - 0.05 * abs(lat) / 90  # Lower at high latitudes
   ```

## Current Behavior Summary

- **Pros:** Fast, no API calls, gives reasonable "typical" patterns
- **Cons:** Not location-specific enough, especially for:
  - High latitude countries (too flat seasonal variation)
  - Countries far from prime meridian (peak time is wrong)
  - Regions with unique weather patterns

The seasonal norm is best used as a **rough reference** to compare against, not as an accurate prediction of what "should" be generated.
