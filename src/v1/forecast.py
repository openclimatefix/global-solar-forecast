"""Functions to get solar forecast data."""

import pandas as pd
import requests
import streamlit as st
from scipy.signal import savgol_filter

data_dir = "src/v1/data"


@st.cache_data(ttl="1h")
def get_forecast(
    name: str,
    capacity: float,
    lat: float,
    lon: float,
) -> pd.DataFrame | None:
    """Get solar forecast for a given location and capacity."""
    if capacity == 0:
        return None

    site = {
        "latitude": lat,
        "longitude": lon,
        "capacity_kwp": capacity,
        "tilt": abs(lat) / 2,
        "orientation": 180 if lat > 0 else 0,
    }
    now = pd.Timestamp.utcnow().floor("h").replace(tzinfo=None).isoformat()
    data = {"site": site, "timestamp": now}
    url = "https://open.quartz.solar/forecast/"

    r = requests.post(url, json=data, timeout=20)

    if r.status_code == 200:
        forecast = r.json()
        predictions: pd.DataFrame = pd.DataFrame(forecast["predictions"])

        # smooth out some of the predictions
        # ideally we would take this out, and the ML model would do this
        zeros = predictions["power_kw"] == 0
        predictions = predictions[["power_kw"]].apply(savgol_filter, window_length=10, polyorder=2)
        predictions.loc[zeros, "power_kw"] = 0

        return predictions
    else:
        st.error(f"Error fetching forecast for {name}")
        return None
