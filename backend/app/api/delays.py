from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RealtimeObservation

router = APIRouter(prefix="/delays", tags=["delays"])


@router.get("/history")
def delay_history(
    route_id: str,
    stop_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = select(RealtimeObservation).where(RealtimeObservation.route_id == route_id)
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
            "scheduled_time": obs.scheduled_time,
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
    filters = [RealtimeObservation.route_id == route_id]
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

    by_hour_rows = db.execute(
        select(
            extract("hour", RealtimeObservation.observed_time).label("hour"),
            func.avg(RealtimeObservation.delay_minutes).label("average_delay"),
            func.count().label("count"),
        )
        .where(*filters)
        .group_by("hour")
        .order_by("hour")
    ).all()
    delay_by_hour = [{"hour": int(row.hour), "average_delay": round(float(row.average_delay or 0), 1), "count": row.count} for row in by_hour_rows]

    by_day_rows = db.execute(
        select(
            extract("dow", RealtimeObservation.observed_time).label("day"),
            func.avg(RealtimeObservation.delay_minutes).label("average_delay"),
            func.count().label("count"),
        )
        .where(*filters)
        .group_by("day")
        .order_by("day")
    ).all()
    day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    delay_by_day = [
        {"day": day_names[int(row.day)], "average_delay": round(float(row.average_delay or 0), 1), "count": row.count}
        for row in by_day_rows
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
