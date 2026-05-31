from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.reliability_service import compute_all_reliability, compute_reliability

router = APIRouter(prefix="/reliability", tags=["reliability"])


@router.get("")
def reliability(
    route_id: str | None = Query(default=None),
    stop_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Reliability for a single route (when route_id is given) or every rail route."""
    if route_id:
        return compute_reliability(db, route_id, stop_id)
    return compute_all_reliability(db)
