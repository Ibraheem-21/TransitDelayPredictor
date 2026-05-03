import os
from pathlib import Path

from dotenv import load_dotenv

from app.database import SessionLocal, init_db
from app.services.gtfs_static_service import download_and_extract_gtfs, import_gtfs_static

load_dotenv()


def main() -> None:
    init_db()
    gtfs_url = os.getenv("GTFS_STATIC_URL")
    if not gtfs_url:
        raise RuntimeError("GTFS_STATIC_URL is required")
    gtfs_dir = download_and_extract_gtfs(gtfs_url, Path("../data"))
    with SessionLocal() as db:
        result = import_gtfs_static(db, gtfs_dir)
    print(result)


if __name__ == "__main__":
    main()
