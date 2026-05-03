from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Route
from app.schemas import RouteOut

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=list[RouteOut])
def list_routes(db: Session = Depends(get_db)) -> list[Route]:
    return list(db.scalars(select(Route).order_by(Route.route_name)).all())
