"""Tool: get_weather.

Live call to Open-Meteo (free, no API key). This is the one genuinely external
dependency in the project — kept because it's free and stable. Returns a tiny
dict the agent can reason over: rain probability + max temp for a given date.
"""
from __future__ import annotations

import requests

# Berlin centre
_LAT, _LON = 52.52, 13.405
_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(date: str) -> dict:
    """Daily forecast for `date` (ISO 'YYYY-MM-DD').

    Returns {"date", "rain_prob", "temp_max", "is_wet"}.
    Open-Meteo only forecasts ~16 days out; for dates outside that range it
    returns rain_prob=None and is_wet=False (treat as 'unknown, allow outdoor').
    """
    params = {
        "latitude": _LAT,
        "longitude": _LON,
        "daily": "precipitation_probability_max,temperature_2m_max",
        "timezone": "Europe/Berlin",
        "start_date": date,
        "end_date": date,
    }
    try:
        r = requests.get(_URL, params=params, timeout=10)
        r.raise_for_status()
        daily = r.json().get("daily", {})
        rain = (daily.get("precipitation_probability_max") or [None])[0]
        temp = (daily.get("temperature_2m_max") or [None])[0]
    except Exception as e:  # network/range failure → fail open, don't crash the graph
        return {"date": date, "rain_prob": None, "temp_max": None,
                "is_wet": False, "error": str(e)}

    return {
        "date": date,
        "rain_prob": rain,
        "temp_max": temp,
        "is_wet": rain is not None and rain >= 60,   # tweak threshold to taste
    }
