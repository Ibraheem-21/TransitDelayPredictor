from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import LIVE_SOURCE
from app.database import get_db
from app.models import RealtimeObservation
from app.services.route_grouping import member_route_ids

router = APIRouter(prefix="/delays", tags=["delays"])
UTC = ZoneInfo("UTC")
LOCAL_TZ = ZoneInfo("America/Toronto")
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def to_local(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(LOCAL_TZ)


def to_local_iso(value: datetime | None) -> str | None:
    local = to_local(value)
    return local.isoformat() if local else None


@router.get("/data-status")
def data_status(db: Session = Depends(get_db)) -> dict:
    source_rows = db.execute(
        select(
            RealtimeObservation.source,
            func.count().label("count"),
            func.min(RealtimeObservation.observed_time).label("earliest_observed_time"),
            func.max(RealtimeObservation.observed_time).label("latest_observed_time"),
        )
        .group_by(RealtimeObservation.source)
        .order_by(RealtimeObservation.source)
    ).all()
    sources = [
        {
            "source": row.source or "unknown",
            "count": row.count,
            "earliest_observed_time": to_local_iso(row.earliest_observed_time),
            "latest_observed_time": to_local_iso(row.latest_observed_time),
        }
        for row in source_rows
    ]
    live = next((source for source in sources if source["source"] == "gtfs-realtime"), None)
    synthetic_count = sum(source["count"] for source in sources if source["source"] == "synthetic")
    return {
        "live_only": synthetic_count == 0,
        "live_source": "Open Metrolinx GTFS Realtime TripUpdates",
        "sources": sources,
        "live_observation_count": live["count"] if live else 0,
        "synthetic_observation_count": synthetic_count,
        "earliest_live_observed_time": live["earliest_observed_time"] if live else None,
        "latest_live_observed_time": live["latest_observed_time"] if live else None,
    }


@router.get("/history")
def delay_history(
    route_id: str,
    stop_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = select(RealtimeObservation).where(
        RealtimeObservation.route_id.in_(member_route_ids(db, route_id)),
        RealtimeObservation.source == LIVE_SOURCE,
    )
    if stop_id:
        stmt = stmt.where(RealtimeObservation.stop_id == stop_id)
    if start_date:
        stmt = stmt.where(RealtimeObservation.observed_time >= start_date)
    if end_date:
        stmt = stmt.where(RealtimeObservation.observed_time <= end_date)

    observations = db.scalars(stmt.order_by(RealtimeObservation.observed_time.desc()).limit(500)).all()
    return [
        {
            "id": obs.id,
            "trip_id": obs.trip_id,
            "route_id": obs.route_id,
            "stop_id": obs.stop_id,
            "observed_time": obs.observed_time,
            "observed_time_local": to_local_iso(obs.observed_time),
            "scheduled_time": obs.scheduled_time,
            "scheduled_time_local": to_local_iso(obs.scheduled_time),
            "delay_minutes": obs.delay_minutes or 0,
            "status": obs.status,
        }
        for obs in observations
    ]


@router.get("/summary")
def delay_summary(
    route_id: str,
    stop_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    filters = [
        RealtimeObservation.route_id.in_(member_route_ids(db, route_id)),
        RealtimeObservation.source == LIVE_SOURCE,
    ]
    if stop_id:
        filters.append(RealtimeObservation.stop_id == stop_id)

    total = db.scalar(select(func.count()).select_from(RealtimeObservation).where(*filters)) or 0
    if total == 0:
        return {
            "average_delay": 0,
            "percent_delayed": 0,
            "most_common_delay_hour": None,
            "worst_day_of_week": None,
            "reliability_score": 100,
            "delay_by_hour": [],
            "delay_by_day": [],
            "sample_size": 0,
        }

    avg_delay = db.scalar(select(func.avg(RealtimeObservation.delay_minutes)).where(*filters)) or 0
    delayed = db.scalar(select(func.count()).select_from(RealtimeObservation).where(*filters, RealtimeObservation.delay_minutes >= 5)) or 0
    percent_delayed = round((delayed / total) * 100, 1)

    rows = db.execute(select(RealtimeObservation.observed_time, RealtimeObservation.delay_minutes).where(*filters)).all()
    by_hour: dict[int, list[float]] = defaultdict(list)
    by_day: dict[int, list[float]] = defaultdict(list)
    for observed_time, delay_minutes in rows:
        local_time = to_local(observed_time)
        if not local_time:
            continue
        delay = float(delay_minutes or 0)
        by_hour[local_time.hour].append(delay)
        by_day[local_time.weekday()].append(delay)

    delay_by_hour = [
        {"hour": hour, "average_delay": round(sum(values) / len(values), 1), "count": len(values)}
        for hour, values in sorted(by_hour.items())
    ]
    delay_by_day = [
        {"day": DAY_NAMES[day], "average_delay": round(sum(values) / len(values), 1), "count": len(values)}
        for day, values in sorted(by_day.items())
    ]

    worst_hour = max(delay_by_hour, key=lambda item: item["average_delay"], default={}).get("hour")
    worst_day = max(delay_by_day, key=lambda item: item["average_delay"], default={}).get("day")

    return {
        "average_delay": round(float(avg_delay), 1),
        "percent_delayed": percent_delayed,
        "most_common_delay_hour": worst_hour,
        "worst_day_of_week": worst_day,
        "reliability_score": round(100 - percent_delayed, 1),
        "delay_by_hour": delay_by_hour,
        "delay_by_day": delay_by_day,
        "sample_size": total,
    }
