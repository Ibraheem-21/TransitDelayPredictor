from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ScheduledStopTime, Stop, Trip
from app.schemas import StopOut

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("", response_model=list[StopOut])
def list_stops(route_id: str | None = Query(default=None), db: Session = Depends(get_db)) -> list[Stop]:
    if not route_id:
        return list(db.scalars(select(Stop).order_by(Stop.stop_name)).all())

    stop_ids = (
        select(ScheduledStopTime.stop_id)
        .join(Trip, ScheduledStopTime.trip_id == Trip.trip_id)
        .where(Trip.route_id == route_id)
        .distinct()
    )
    return list(db.scalars(select(Stop).where(Stop.stop_id.in_(stop_ids)).order_by(Stop.stop_name)).all())
