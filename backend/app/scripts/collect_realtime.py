import os

from dotenv import load_dotenv

from app.database import SessionLocal, init_db
from app.services.gtfs_realtime_service import collect_trip_updates

load_dotenv()


def main() -> None:
    init_db()
    url = os.getenv("GTFS_REALTIME_TRIP_UPDATES_URL")
    if not url:
        raise RuntimeError("GTFS_REALTIME_TRIP_UPDATES_URL is required")
    with SessionLocal() as db:
        count = collect_trip_updates(db, url)
    print(f"stored {count} realtime observations")


if __name__ == "__main__":
    main()
