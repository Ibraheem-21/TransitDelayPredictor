from datetime import datetime
import os

import requests
from google.transit import gtfs_realtime_pb2
from requests import HTTPError
from sqlalchemy.orm import Session

from app.models import RealtimeObservation, ServiceAlert


def fetch_feed(url: str) -> gtfs_realtime_pb2.FeedMessage:
    api_key = os.getenv("OPENMETROLINX_API_KEY")
    params = {"key": api_key} if api_key else None
    response = requests.get(url, params=params, headers={"Accept": "application/x-protobuf"}, timeout=30)
    try:
        response.raise_for_status()
    except HTTPError as exc:
        raise RuntimeError(f"Open Metrolinx request failed with HTTP {response.status_code}") from exc
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    return feed


def collect_trip_updates(db: Session, url: str) -> int:
    feed = fetch_feed(url)
    count = 0
    observed_time = datetime.utcnow()
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        update = entity.trip_update
        trip_id = update.trip.trip_id or None
        route_id = update.trip.route_id or None
        for stop_update in update.stop_time_update:
            delay_seconds = None
            scheduled_time = None
            if stop_update.HasField("arrival"):
                delay_seconds = stop_update.arrival.delay
                scheduled_time = datetime.utcfromtimestamp(stop_update.arrival.time) if stop_update.arrival.time else None
            elif stop_update.HasField("departure"):
                delay_seconds = stop_update.departure.delay
                scheduled_time = datetime.utcfromtimestamp(stop_update.departure.time) if stop_update.departure.time else None
            db.add(
                RealtimeObservation(
                    trip_id=trip_id,
                    route_id=route_id,
                    stop_id=stop_update.stop_id or None,
                    observed_time=observed_time,
                    scheduled_time=scheduled_time,
                    delay_seconds=delay_seconds,
                    delay_minutes=round((delay_seconds or 0) / 60, 1),
                    status=str(stop_update.schedule_relationship),
                    source="gtfs-realtime",
                )
            )
            count += 1
    db.commit()
    return count


def collect_service_alerts(db: Session, url: str) -> int:
    feed = fetch_feed(url)
    count = 0
    db.query(ServiceAlert).delete()
    for entity in feed.entity:
        if not entity.HasField("alert"):
            continue
        alert = entity.alert
        header = alert.header_text.translation[0].text if alert.header_text.translation else None
        description = alert.description_text.translation[0].text if alert.description_text.translation else None
        start_time = datetime.utcfromtimestamp(alert.active_period[0].start) if alert.active_period and alert.active_period[0].start else None
        end_time = datetime.utcfromtimestamp(alert.active_period[0].end) if alert.active_period and alert.active_period[0].end else None
        informed_entities = alert.informed_entity or [None]
        for informed in informed_entities:
            db.add(
                ServiceAlert(
                    route_id=getattr(informed, "route_id", None) if informed else None,
                    stop_id=getattr(informed, "stop_id", None) if informed else None,
                    alert_header=header,
                    alert_description=description,
                    cause=str(alert.cause),
                    effect=str(alert.effect),
                    start_time=start_time,
                    end_time=end_time,
                )
            )
            count += 1
    db.commit()
    return count
