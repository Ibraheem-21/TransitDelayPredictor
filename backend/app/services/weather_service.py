from datetime import datetime
import os

import requests
from sqlalchemy.orm import Session

from app.models import WeatherObservation

GO_WEATHER_CITIES = [
    "Toronto",
    "Mississauga",
    "Oakville",
    "Burlington",
    "Hamilton",
    "Pickering",
    "Ajax",
    "Oshawa",
    "Brampton",
    "Kitchener",
]


def _as_float(value: object, default: float = 0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _weather_description(value: object) -> str | None:
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return first.get("value")
        return str(first)
    if isinstance(value, str):
        return value
    return None


def _collect_world_weather_online(db: Session, api_key: str, cities: list[str]) -> int:
    count = 0
    for city in cities:
        response = requests.get(
            "https://api.worldweatheronline.com/premium/v1/weather.ashx",
            params={
                "key": api_key,
                "q": f"{city},Canada",
                "format": "json",
                "num_of_days": 1,
                "fx": "no",
                "cc": "yes",
                "mca": "no",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        condition = payload.get("data", {}).get("current_condition", [{}])[0]
        description = _weather_description(condition.get("weatherDesc")) or ""
        precipitation = _as_float(condition.get("precipMM"))
        is_snow = "snow" in description.lower()
        is_rain = any(term in description.lower() for term in ["rain", "drizzle", "shower"])
        db.add(
            WeatherObservation(
                station_or_city=city,
                observed_time=datetime.utcnow(),
                temperature=_as_float(condition.get("temp_C")),
                precipitation=precipitation,
                wind_speed=_as_float(condition.get("windspeedKmph")),
                snow=precipitation if is_snow else 0,
                rain=precipitation if is_rain else 0,
                weather_main=description.split(" ")[0] if description else None,
                weather_description=description or None,
            )
        )
        count += 1
    db.commit()
    return count


def _collect_openweather(db: Session, api_key: str, cities: list[str]) -> int:
    count = 0
    for city in cities:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": f"{city},CA", "appid": api_key, "units": "metric"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        weather = payload.get("weather", [{}])[0]
        db.add(
            WeatherObservation(
                station_or_city=city,
                observed_time=datetime.utcfromtimestamp(payload.get("dt", datetime.utcnow().timestamp())),
                temperature=payload.get("main", {}).get("temp"),
                precipitation=(payload.get("rain", {}).get("1h") or 0) + (payload.get("snow", {}).get("1h") or 0),
                wind_speed=payload.get("wind", {}).get("speed"),
                snow=payload.get("snow", {}).get("1h", 0),
                rain=payload.get("rain", {}).get("1h", 0),
                weather_main=weather.get("main"),
                weather_description=weather.get("description"),
            )
        )
        count += 1
    db.commit()
    return count


def collect_current_weather(db: Session, api_key: str, cities: list[str] | None = None) -> int:
    selected_cities = cities or GO_WEATHER_CITIES
    if os.getenv("WORLDWEATHERONLINE_API_KEY"):
        return _collect_world_weather_online(db, api_key, selected_cities)
    return _collect_openweather(db, api_key, selected_cities)
