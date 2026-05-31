"""Group GO rail schedule-version duplicates into a single canonical line.

GO Transit's GTFS publishes the same rail line under several route_ids, one per
schedule period (e.g. ``04260626-LW`` and ``06260926-LW`` are both Lakeshore
West). The realtime feed only emits the route_id of the active period, so
without grouping each line shows up twice with half the entries permanently
empty. These helpers collapse the variants by their line code (the suffix after
the last ``-``) and aggregate observations across every member route_id, which
also keeps history intact when GO rolls over to a new schedule period.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import RAIL_ROUTE_TYPE
from app.models import Route


def line_key(route_id: str) -> str:
    """Canonical line code for a route_id, e.g. ``04260626-LW`` -> ``LW``."""
    if not route_id:
        return route_id
    return route_id.rsplit("-", 1)[-1]


def _rail_routes(db: Session) -> list[Route]:
    return list(db.scalars(select(Route).where(Route.route_type == RAIL_ROUTE_TYPE)).all())


def member_route_ids(db: Session, route_id: str) -> list[str]:
    """All route_ids that belong to the same line as ``route_id``."""
    key = line_key(route_id)
    members = [route.route_id for route in _rail_routes(db) if line_key(route.route_id) == key]
    return members or [route_id]


def canonical_routes(db: Session) -> list[Route]:
    """One representative Route per rail line, sorted by name."""
    groups: dict[str, list[Route]] = {}
    for route in _rail_routes(db):
        groups.setdefault(line_key(route.route_id), []).append(route)
    representatives = [sorted(group, key=lambda route: route.route_id)[0] for group in groups.values()]
    representatives.sort(key=lambda route: route.route_name)
    return representatives
