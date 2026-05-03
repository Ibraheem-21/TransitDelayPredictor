import os

from dotenv import load_dotenv

from app.database import SessionLocal, init_db
from app.services.weather_service import collect_current_weather

load_dotenv()


def main() -> None:
    init_db()
    api_key = os.getenv("WORLDWEATHERONLINE_API_KEY") or os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise RuntimeError("WORLDWEATHERONLINE_API_KEY or OPENWEATHER_API_KEY is required")
    with SessionLocal() as db:
        count = collect_current_weather(db, api_key)
    print(f"stored {count} weather observations")


if __name__ == "__main__":
    main()
