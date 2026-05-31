"""Route reliability scoring.

Produces a 0-100 reliability score plus a High/Medium/Low grade and a list of
plain-language reasons for each rail route. Scores are derived only from
collected GTFS Realtime observations and service alerts, so they reflect real
history rather than hardcoded values. Routes without enough data are reported
with low confidence and an explicit reason instead of a fabricated score.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import DELAY_THRESHOLD_MINUTES, LIVE_SOURCE
from app.models import RealtimeObservation, ServiceAlert
from app.services.route_grouping import canonical_routes, member_route_ids

# Below this many observations the score is informational only.
MIN_CONFIDENT_SAMPLE = 50
RECENT_WINDOW_HOURS = 24

# Penalty weights (points subtracted from a perfect 100).
MAX_FREQUENCY_PENALTY = 45
MAX_AVG_DELAY_PENALTY = 25
MAX_ALERT_PENALTY = 15
MAX_RECENT_PENALTY = 15
MAX_CANCELLATION_PENALTY = 20


def _grade(score: float) -> str:
    if score >= 75:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def _route_filters(members: list[str], stop_id: str | None = None) -> list:
    filters = [
        RealtimeObservation.route_id.in_(members),
        RealtimeObservation.source == LIVE_SOURCE,
    ]
    if stop_id:
        filters.append(RealtimeObservation.stop_id == stop_id)
    return filters


def compute_reliability(db: Session, route_id: str, stop_id: str | None = None) -> dict:
    members = member_route_ids(db, route_id)
    filters = _route_filters(members, stop_id)

    total = db.scalar(select(func.count()).select_from(RealtimeObservation).where(*filters)) or 0
    if total == 0:
        return {
            "route_id": route_id,
            "score": None,
            "grade": "Unknown",
            "confidence": "none",
            "reasons": ["No live observations collected yet for this route."],
            "components": {
                "delay_frequency_pct": 0.0,
                "avg_delay_minutes": 0.0,
                "cancellation_pct": 0.0,
                "active_alert_count": 0,
                "recent_avg_delay_minutes": 0.0,
                "sample_size": 0,
            },
        }

    avg_delay = float(db.scalar(select(func.avg(RealtimeObservation.delay_minutes)).where(*filters)) or 0)
    delayed = db.scalar(
        select(func.count())
        .select_from(RealtimeObservation)
        .where(*filters, RealtimeObservation.delay_minutes >= DELAY_THRESHOLD_MINUTES)
    ) or 0
    cancelled = db.scalar(
        select(func.count())
        .select_from(RealtimeObservation)
        .where(*filters, RealtimeObservation.status == "CANCELED")
    ) or 0

    recent_since = datetime.utcnow() - timedelta(hours=RECENT_WINDOW_HOURS)
    recent_avg = db.scalar(
        select(func.avg(RealtimeObservation.delay_minutes)).where(
            *filters, RealtimeObservation.observed_time >= recent_since
        )
    )
    recent_avg = float(recent_avg) if recent_avg is not None else avg_delay

    active_alerts = db.scalar(
        select(func.count())
        .select_from(ServiceAlert)
        .where(
            (ServiceAlert.route_id.in_(members)) | (ServiceAlert.route_id.is_(None)),
            (ServiceAlert.end_time.is_(None)) | (ServiceAlert.end_time >= datetime.utcnow()),
        )
    ) or 0

    delay_frequency_pct = round((delayed / total) * 100, 1)
    cancellation_pct = round((cancelled / total) * 100, 1)

    # Convert each metric into a bounded penalty, then subtract from 100.
    frequency_penalty = min(MAX_FREQUENCY_PENALTY, delay_frequency_pct * 0.6)
    avg_delay_penalty = min(MAX_AVG_DELAY_PENALTY, max(0.0, avg_delay) * 2.5)
    alert_penalty = min(MAX_ALERT_PENALTY, active_alerts * 5)
    recent_penalty = min(MAX_RECENT_PENALTY, max(0.0, recent_avg) * 2.0)
    cancellation_penalty = min(MAX_CANCELLATION_PENALTY, cancellation_pct * 1.5)

    score = round(
        max(
            0.0,
            100
            - frequency_penalty
            - avg_delay_penalty
            - alert_penalty
            - recent_penalty
            - cancellation_penalty,
        ),
        1,
    )

    reasons: list[str] = []
    reasons.append(f"{delay_frequency_pct}% of trips ran 5+ minutes late.")
    reasons.append(f"Average delay of {round(avg_delay, 1)} minutes across {total} observations.")
    if cancellation_pct > 0:
        reasons.append(f"{cancellation_pct}% of observed trips were cancelled.")
    if active_alerts > 0:
        reasons.append(f"{active_alerts} active service alert(s) affecting this route.")
    if recent_avg >= DELAY_THRESHOLD_MINUTES:
        reasons.append(f"Recent {RECENT_WINDOW_HOURS}h delays are elevated ({round(recent_avg, 1)} min average).")
    elif recent_avg <= 1 and avg_delay <= 1:
        reasons.append("Trains have been running close to schedule recently.")

    confidence = "high" if total >= MIN_CONFIDENT_SAMPLE * 4 else "medium" if total >= MIN_CONFIDENT_SAMPLE else "low"
    if confidence == "low":
        reasons.append(f"Limited history ({total} observations); score may change as more data is collected.")

    return {
        "route_id": route_id,
        "score": score,
        "grade": _grade(score),
        "confidence": confidence,
        "reasons": reasons,
        "components": {
            "delay_frequency_pct": delay_frequency_pct,
            "avg_delay_minutes": round(avg_delay, 1),
            "cancellation_pct": cancellation_pct,
            "active_alert_count": active_alerts,
            "recent_avg_delay_minutes": round(recent_avg, 1),
            "sample_size": total,
        },
    }


def compute_all_reliability(db: Session) -> list[dict]:
    """Reliability for every rail line, sorted best-first for comparison views."""
    results: list[dict] = []
    for route in canonical_routes(db):
        reliability = compute_reliability(db, route.route_id)
        reliability["route_name"] = route.route_name
        results.append(reliability)

    # Sort routes with a score first (highest reliability first); unknowns last.
    results.sort(key=lambda item: (item["score"] is None, -(item["score"] or 0)))
    return results
