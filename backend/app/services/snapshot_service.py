"""Per-route snapshots combining live status, prediction, reliability, alerts.

This powers the dashboard's route snapshot grid. Every value comes from
collected data or the prediction/reliability services; nothing is hardcoded.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import ServiceAlert
from app.services.prediction_service import estimate_baseline, get_live_status, risk_label
from app.services.reliability_service import compute_reliability
from app.services.route_grouping import canonical_routes, member_route_ids

LOCAL_TZ = ZoneInfo("America/Toronto")
UTC = ZoneInfo("UTC")


def _to_local_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(LOCAL_TZ).isoformat()


def _recent_alerts(db: Session, route_id: str) -> list[dict]:
    now = datetime.utcnow()
    stmt = (
        select(ServiceAlert)
        .where(
            or_(ServiceAlert.end_time.is_(None), ServiceAlert.end_time >= now),
            or_(ServiceAlert.route_id.in_(member_route_ids(db, route_id)), ServiceAlert.route_id.is_(None)),
        )
        .order_by(ServiceAlert.created_at.desc())
        .limit(5)
    )
    return [
        {
            "id": alert.id,
            "header": alert.alert_header,
            "description": alert.alert_description,
            "effect": alert.effect,
        }
        for alert in db.scalars(stmt).all()
    ]


def build_route_snapshots(db: Session) -> list[dict]:
    now = datetime.utcnow()
    snapshots: list[dict] = []
    for route in canonical_routes(db):
        live = get_live_status(db, route.route_id)
        probability, expected_minutes, _sample, is_data_driven = estimate_baseline(db, route.route_id, now)
        reliability = compute_reliability(db, route.route_id)
        alerts = _recent_alerts(db, route.route_id)

        snapshots.append(
            {
                "route_id": route.route_id,
                "route_name": route.route_name,
                "live_status": live.status,
                "live_average_delay_minutes": live.average_delay_minutes,
                "predicted_risk": risk_label(probability),
                "predicted_probability": probability,
                "predicted_delay_minutes": expected_minutes,
                "prediction_is_data_driven": is_data_driven,
                "average_recent_delay_minutes": reliability["components"]["recent_avg_delay_minutes"],
                "reliability_score": reliability["score"],
                "reliability_grade": reliability["grade"],
                "recent_alerts": alerts,
                "alert_count": len(alerts),
                "last_updated": _to_local_iso(live.last_updated),
                "sample_size": reliability["components"]["sample_size"],
            }
        )

    # Most relevant routes first: alerts, then worst current delays.
    snapshots.sort(key=lambda s: (-s["alert_count"], -s["live_average_delay_minutes"]))
    return snapshots
