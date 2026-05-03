import os

from dotenv import load_dotenv

from app.database import SessionLocal, init_db
from app.services.gtfs_realtime_service import collect_service_alerts

load_dotenv()


def main() -> None:
    init_db()
    url = os.getenv("GTFS_REALTIME_ALERTS_URL")
    if not url:
        raise RuntimeError("GTFS_REALTIME_ALERTS_URL is required")
    with SessionLocal() as db:
        count = collect_service_alerts(db, url)
    print(f"stored {count} service alerts")


if __name__ == "__main__":
    main()
