import os
import time
from datetime import datetime

import requests
from google.transit import gtfs_realtime_pb2
from requests import HTTPError, RequestException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import LIVE_SOURCE, MAX_PLAUSIBLE_DELAY_SECONDS, RAIL_ROUTE_TYPE
from app.models import RealtimeObservation, Route, ServiceAlert

# Open Metrolinx feeds refresh roughly once per minute. Re-fetching faster than
# this wastes the request budget, so a short TTL cache serves the last payload.
FEED_CACHE_TTL_SECONDS = 25
# Retry transient failures (429 rate limit, 5xx) with exponential backoff.
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 2

_feed_cache: dict[str, tuple[float, bytes]] = {}

# GTFS-RT trip schedule_relationship value for a cancelled trip.
_TRIP_CANCELED = 3


def _rail_route_ids(db: Session) -> set[str]:
    """Route IDs for rail service, used to discard bus data from live feeds."""
    return set(db.scalars(select(Route.route_id).where(Route.route_type == RAIL_ROUTE_TYPE)).all())


def fetch_feed(url: str, *, use_cache: bool = True) -> gtfs_realtime_pb2.FeedMessage:
    """Fetch and parse a GTFS Realtime feed with caching and retry/backoff."""
    now = time.monotonic()
    if use_cache:
        cached = _feed_cache.get(url)
        if cached and now - cached[0] < FEED_CACHE_TTL_SECONDS:
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(cached[1])
            return feed

    api_key = os.getenv("OPENMETROLINX_API_KEY")
    params = {"key": api_key} if api_key else None
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                url,
                params=params,
                headers={"Accept": "application/x-protobuf"},
                timeout=30,
            )
            if response.status_code == 429 or response.status_code >= 500:
                # Rate limited or upstream error: back off and retry.
                last_error = RuntimeError(
                    f"Open Metrolinx request failed with HTTP {response.status_code}"
                )
                time.sleep(BACKOFF_BASE_SECONDS * (2**attempt))
                continue
            response.raise_for_status()
        except HTTPError as exc:
            raise RuntimeError(
                f"Open Metrolinx request failed with HTTP {response.status_code}"
            ) from exc
        except RequestException as exc:
            last_error = exc
            time.sleep(BACKOFF_BASE_SECONDS * (2**attempt))
            continue

        _feed_cache[url] = (now, response.content)
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        return feed

    raise RuntimeError(f"Open Metrolinx request failed after {MAX_RETRIES} attempts") from last_error


def _valid_delay_seconds(delay_seconds: int | None) -> int | None:
    """Discard implausible delay values that would corrupt aggregates."""
    if delay_seconds is None:
        return None
    if abs(delay_seconds) > MAX_PLAUSIBLE_DELAY_SECONDS:
        return None
    return delay_seconds


def collect_trip_updates(db: Session, url: str) -> int:
    feed = fetch_feed(url)
    rail_route_ids = _rail_route_ids(db)
    count = 0
    observed_time = datetime.utcnow()
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        update = entity.trip_update
        trip_id = update.trip.trip_id or None
        route_id = update.trip.route_id or None

        # Rail-only app: skip bus routes once the rail route list is known.
        if rail_route_ids and route_id is not None and route_id not in rail_route_ids:
            continue

        trip_cancelled = update.trip.schedule_relationship == _TRIP_CANCELED

        for stop_update in update.stop_time_update:
            delay_seconds = None
            scheduled_time = None
            if stop_update.HasField("arrival"):
                delay_seconds = stop_update.arrival.delay
                scheduled_time = datetime.utcfromtimestamp(stop_update.arrival.time) if stop_update.arrival.time else None
            elif stop_update.HasField("departure"):
                delay_seconds = stop_update.departure.delay
                scheduled_time = datetime.utcfromtimestamp(stop_update.departure.time) if stop_update.departure.time else None

            delay_seconds = _valid_delay_seconds(delay_seconds)
            status = "CANCELED" if trip_cancelled else str(stop_update.schedule_relationship)
            db.add(
                RealtimeObservation(
                    trip_id=trip_id,
                    route_id=route_id,
                    stop_id=stop_update.stop_id or None,
                    observed_time=observed_time,
                    scheduled_time=scheduled_time,
                    delay_seconds=delay_seconds,
                    delay_minutes=round((delay_seconds or 0) / 60, 1),
                    status=status,
                    source=LIVE_SOURCE,
                )
            )
            count += 1
    db.commit()
    return count


def collect_service_alerts(db: Session, url: str) -> int:
    feed = fetch_feed(url)
    rail_route_ids = _rail_route_ids(db)
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
            route_id = getattr(informed, "route_id", None) if informed else None
            route_id = route_id or None
            stop_id = getattr(informed, "stop_id", None) if informed else None
            stop_id = stop_id or None

            # Keep rail-specific alerts and network-wide alerts (no route_id).
            if rail_route_ids and route_id is not None and route_id not in rail_route_ids:
                continue

            db.add(
                ServiceAlert(
                    route_id=route_id,
                    stop_id=stop_id,
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
