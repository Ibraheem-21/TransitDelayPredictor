from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests
from sqlalchemy.orm import Session

from app.models import Route, ScheduledStopTime, Stop, Trip


def download_and_extract_gtfs(url: str, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir / "gtfs_static.zip"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    zip_path.write_bytes(response.content)
    extract_dir = target_dir / "gtfs_static"
    extract_dir.mkdir(exist_ok=True)
    with ZipFile(zip_path) as archive:
        archive.extractall(extract_dir)
    return extract_dir


def import_gtfs_static(db: Session, gtfs_dir: Path) -> dict[str, int]:
    routes = pd.read_csv(gtfs_dir / "routes.txt")
    stops = pd.read_csv(gtfs_dir / "stops.txt")
    trips = pd.read_csv(gtfs_dir / "trips.txt")
    stop_times = pd.read_csv(gtfs_dir / "stop_times.txt", usecols=["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"])

    db.query(ScheduledStopTime).delete()
    db.query(Trip).delete()
    db.query(Stop).delete()
    db.query(Route).delete()

    db.bulk_save_objects([
        Route(
            route_id=str(row.route_id),
            route_name=str(getattr(row, "route_long_name", None) or getattr(row, "route_short_name", row.route_id)),
            route_type=str(getattr(row, "route_type", "")),
            agency=str(getattr(row, "agency_id", "GO Transit")),
        )
        for row in routes.itertuples()
    ])
    db.bulk_save_objects([
        Stop(
            stop_id=str(row.stop_id),
            stop_name=str(row.stop_name),
            latitude=float(row.stop_lat) if pd.notna(row.stop_lat) else None,
            longitude=float(row.stop_lon) if pd.notna(row.stop_lon) else None,
        )
        for row in stops.itertuples()
    ])
    db.bulk_save_objects([
        Trip(
            trip_id=str(row.trip_id),
            route_id=str(row.route_id),
            service_id=str(getattr(row, "service_id", "")),
            direction_id=str(getattr(row, "direction_id", "")),
            trip_headsign=str(getattr(row, "trip_headsign", "")),
        )
        for row in trips.itertuples()
    ])
    db.bulk_save_objects([
        ScheduledStopTime(
            trip_id=str(row.trip_id),
            stop_id=str(row.stop_id),
            scheduled_arrival=str(row.arrival_time),
            scheduled_departure=str(row.departure_time),
            stop_sequence=int(row.stop_sequence) if pd.notna(row.stop_sequence) else None,
        )
        for row in stop_times.itertuples()
    ])
    db.commit()
    return {"routes": len(routes), "stops": len(stops), "trips": len(trips), "stop_times": len(stop_times)}
