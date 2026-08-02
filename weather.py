from __future__ import annotations

import requests

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Light rain showers",
    81: "Rain showers",
    82: "Heavy rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm with hail",
}


def get_weather(latitude: float, longitude: float, timezone_name: str) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone_name,
        "forecast_days": 1,
        "daily": ",".join(
            [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "uv_index_max",
                "sunrise",
                "sunset",
            ]
        ),
    }
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params=params,
        timeout=20,
    )
    response.raise_for_status()
    daily = response.json()["daily"]

    code = daily["weather_code"][0]
    rain = daily["precipitation_probability_max"][0]
    advice = "A normal day outside."
    if rain >= 60:
        advice = "Carry an umbrella; rain is likely."
    elif rain >= 30:
        advice = "Keep an umbrella nearby; some rain is possible."
    elif daily["uv_index_max"][0] >= 7:
        advice = "Strong UV expected; use sunscreen and stay hydrated."

    return {
        "condition": WEATHER_CODES.get(code, f"Weather code {code}"),
        "max_temp": round(daily["temperature_2m_max"][0]),
        "min_temp": round(daily["temperature_2m_min"][0]),
        "rain_probability": rain,
        "wind_speed": round(daily["wind_speed_10m_max"][0]),
        "uv_index": round(daily["uv_index_max"][0], 1),
        "sunrise": daily["sunrise"][0].split("T")[-1],
        "sunset": daily["sunset"][0].split("T")[-1],
        "advice": advice,
    }
