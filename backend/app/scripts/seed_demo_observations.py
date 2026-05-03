from datetime import datetime, timedelta
import random

from sqlalchemy import select

from app.database import SessionLocal, init_db
from app.models import RealtimeObservation, ScheduledStopTime, Trip, WeatherObservation
from app.services.weather_service import GO_WEATHER_CITIES


def rush_hour(dt: datetime) -> bool:
    minutes = dt.hour * 60 + dt.minute
    return (6 * 60 + 30 <= minutes <= 9 * 60 + 30) or (15 * 60 + 30 <= minutes <= 18 * 60 + 30)


def sample_delay(route_id: str, dt: datetime) -> float:
    route_bias = (sum(ord(char) for char in route_id) % 7) * 0.45
    base = random.gauss(2.0 + route_bias, 2.0)
    if rush_hour(dt):
        base += random.uniform(2.0, 7.0)
    if dt.weekday() >= 5:
        base -= random.uniform(0.5, 2.0)
    if random.random() < 0.08:
        base += random.uniform(8.0, 22.0)
    return round(max(0, base), 1)


def main() -> None:
    init_db()
    random.seed(42)
    with SessionLocal() as db:
        rows = db.execute(
            select(Trip.route_id, ScheduledStopTime.trip_id, ScheduledStopTime.stop_id)
            .join(ScheduledStopTime, ScheduledStopTime.trip_id == Trip.trip_id)
            .limit(25000)
        ).all()
        if not rows:
            raise RuntimeError("Import GTFS static data before seeding demo observations.")

        existing = db.query(RealtimeObservation).filter(RealtimeObservation.source == "synthetic").count()
        if existing:
            print(f"synthetic observations already exist: {existing}")
            return

        now = datetime.utcnow()
        observations = []
        for _ in range(4000):
            route_id, trip_id, stop_id = random.choice(rows)
            observed_time = now - timedelta(
                days=random.randint(0, 45),
                hours=random.randint(0, 23),
                minutes=random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]),
            )
            delay_minutes = sample_delay(route_id, observed_time)
            observations.append(
                RealtimeObservation(
                    trip_id=trip_id,
                    route_id=route_id,
                    stop_id=stop_id,
                    observed_time=observed_time,
                    scheduled_time=observed_time - timedelta(minutes=delay_minutes),
                    delay_seconds=int(delay_minutes * 60),
                    delay_minutes=delay_minutes,
                    status="demo",
                    source="synthetic",
                )
            )

        weather = []
        for day in range(0, 45):
            for city in GO_WEATHER_CITIES:
                observed_time = now - timedelta(days=day, hours=random.randint(0, 23))
                rain = random.choice([0, 0, 0, 0.2, 0.6, 1.4])
                snow = random.choice([0, 0, 0, 0, 0.3]) if observed_time.month in [11, 12, 1, 2, 3] else 0
                weather.append(
                    WeatherObservation(
                        station_or_city=city,
                        observed_time=observed_time,
                        temperature=round(random.uniform(-6, 26), 1),
                        precipitation=rain + snow,
                        wind_speed=round(random.uniform(4, 38), 1),
                        snow=snow,
                        rain=rain,
                        weather_main="Rain" if rain else "Snow" if snow else "Clear",
                        weather_description="demo weather observation",
                    )
                )

        db.bulk_save_objects(observations)
        db.bulk_save_objects(weather)
        db.commit()
        print(f"seeded {len(observations)} synthetic delay observations and {len(weather)} weather observations")


if __name__ == "__main__":
    main()
