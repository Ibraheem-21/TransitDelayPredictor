from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ServiceAlert
from app.schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(route_id: str | None = Query(default=None), db: Session = Depends(get_db)) -> list[ServiceAlert]:
    now = datetime.utcnow()
    stmt = select(ServiceAlert).where(or_(ServiceAlert.end_time.is_(None), ServiceAlert.end_time >= now))
    if route_id:
        stmt = stmt.where(or_(ServiceAlert.route_id == route_id, ServiceAlert.route_id.is_(None)))
    return list(db.scalars(stmt.order_by(ServiceAlert.created_at.desc()).limit(50)).all())
