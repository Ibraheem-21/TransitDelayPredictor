from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Route
from app.schemas import RouteOut
from app.services.route_grouping import canonical_routes
from app.services.snapshot_service import build_route_snapshots

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=list[RouteOut])
def list_routes(db: Session = Depends(get_db)) -> list[Route]:
    """Return GO rail lines (GTFS route_type 2), one entry per line."""
    return canonical_routes(db)


@router.get("/snapshots")
def route_snapshots(db: Session = Depends(get_db)) -> list[dict]:
    """Per-route snapshot: live status, predicted risk, reliability, alerts, last updated."""
    return build_route_snapshots(db)
