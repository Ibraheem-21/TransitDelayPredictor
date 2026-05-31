from datetime import datetime, timedelta
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import DELAY_THRESHOLD_MINUTES, LIVE_SOURCE
from app.models import PredictionLog, RealtimeObservation, ServiceAlert, WeatherObservation
from app.schemas import LiveStatus, PredictionRequest, PredictionResponse
from app.services.route_grouping import member_route_ids

CLASSIFIER_PATH = Path("models/delay_classifier.pkl")
REGRESSOR_PATH = Path("models/delay_regressor.pkl")

# How recent an observation must be to count as the route's "live" status.
LIVE_WINDOW_MINUTES = 90


def is_rush_hour(value: datetime) -> bool:
    minutes = value.hour * 60 + value.minute
    return (6 * 60 + 30 <= minutes <= 9 * 60 + 30) or (15 * 60 + 30 <= minutes <= 18 * 60 + 30)


def risk_label(probability: float) -> str:
    if probability > 0.6:
        return "High"
    if probability > 0.3:
        return "Medium"
    return "Low"


def _confidence(sample_size: int, model_used: bool) -> str:
    if model_used and sample_size >= 200:
        return "high"
    if sample_size >= 50:
        return "medium"
    return "low"


def _range(expected: float) -> str:
    low = max(0, round(expected - 3))
    high = max(low + 1, round(expected + 4))
    return f"{low}-{high} minutes"


def get_live_status(db: Session, route_id: str, stop_id: str | None = None) -> LiveStatus:
    """Current, observed delay state for a route (distinct from prediction)."""
    filters = [
        RealtimeObservation.route_id.in_(member_route_ids(db, route_id)),
        RealtimeObservation.source == LIVE_SOURCE,
    ]
    if stop_id:
        filters.append(RealtimeObservation.stop_id == stop_id)

    since = datetime.utcnow() - timedelta(minutes=LIVE_WINDOW_MINUTES)
    recent_filters = [*filters, RealtimeObservation.observed_time >= since]

    sample = db.scalar(select(func.count()).select_from(RealtimeObservation).where(*recent_filters)) or 0
    last_observed = db.scalar(
        select(func.max(RealtimeObservation.observed_time)).where(*filters)
    )

    if sample == 0:
        return LiveStatus(
            status="No live data",
            average_delay_minutes=0.0,
            sample_size=0,
            last_updated=last_observed,
        )

    avg_delay = float(db.scalar(select(func.avg(RealtimeObservation.delay_minutes)).where(*recent_filters)) or 0)
    cancelled = db.scalar(
        select(func.count())
        .select_from(RealtimeObservation)
        .where(*recent_filters, RealtimeObservation.status == "CANCELED")
    ) or 0

    if cancelled > 0:
        status = "Cancellations reported"
    elif avg_delay >= 10:
        status = "Major delays"
    elif avg_delay >= DELAY_THRESHOLD_MINUTES:
        status = "Minor delays"
    else:
        status = "On time"

    return LiveStatus(
        status=status,
        average_delay_minutes=round(avg_delay, 1),
        sample_size=sample,
        last_updated=last_observed,
    )


def estimate_baseline(
    db: Session, route_id: str, when: datetime, stop_id: str | None = None
) -> tuple[float, float, int, bool]:
    """Return (probability, expected_minutes, sample_size, is_data_driven).

    When no history exists, a clearly-flagged heuristic default is returned so
    callers never mistake it for a real, data-backed estimate.
    """
    members = member_route_ids(db, route_id)
    filters = [RealtimeObservation.route_id.in_(members), RealtimeObservation.source == LIVE_SOURCE]
    if stop_id:
        filters.append(RealtimeObservation.stop_id == stop_id)

    total = db.scalar(select(func.count()).select_from(RealtimeObservation).where(*filters)) or 0
    if total == 0:
        base_probability = 0.35 if is_rush_hour(when) else 0.18
        base_minutes = 6.0 if is_rush_hour(when) else 3.0
        return base_probability, base_minutes, 0, False

    delayed = db.scalar(
        select(func.count())
        .select_from(RealtimeObservation)
        .where(*filters, RealtimeObservation.delay_minutes >= DELAY_THRESHOLD_MINUTES)
    ) or 0
    avg_delay = float(db.scalar(select(func.avg(RealtimeObservation.delay_minutes)).where(*filters)) or 0)
    probability = delayed / total

    if is_rush_hour(when):
        probability = min(1, probability + 0.12)
        avg_delay += 2

    weather = db.scalar(select(WeatherObservation).order_by(WeatherObservation.observed_time.desc()).limit(1))
    if weather:
        if (weather.rain or 0) > 0 or (weather.precipitation or 0) >= 1:
            probability = min(1, probability + 0.07)
            avg_delay += 1
        if (weather.snow or 0) > 0:
            probability = min(1, probability + 0.12)
            avg_delay += 2
        if (weather.wind_speed or 0) >= 35:
            probability = min(1, probability + 0.05)
            avg_delay += 1

    # An active alert raises predicted risk even if averages look calm.
    active_alert = db.scalar(
        select(func.count())
        .select_from(ServiceAlert)
        .where(
            ServiceAlert.route_id.in_(members),
            (ServiceAlert.end_time.is_(None)) | (ServiceAlert.end_time >= datetime.utcnow()),
        )
    ) or 0
    if active_alert:
        probability = min(1, probability + 0.1)
        avg_delay += 1

    return round(probability, 2), round(avg_delay, 1), total, True


def _top_factors(db: Session, payload: PredictionRequest) -> list[str]:
    members = member_route_ids(db, payload.route_id)
    factors: list[str] = []
    if is_rush_hour(payload.datetime):
        factors.append("rush hour")

    recent_since = datetime.utcnow() - timedelta(minutes=30)
    recent_avg = db.scalar(
        select(func.avg(RealtimeObservation.delay_minutes)).where(
            RealtimeObservation.route_id.in_(members),
            RealtimeObservation.source == LIVE_SOURCE,
            RealtimeObservation.observed_time >= recent_since,
        )
    )
    if recent_avg and recent_avg >= 5:
        factors.append("recent route delays")

    active_alert = db.scalar(
        select(func.count()).select_from(ServiceAlert).where(
            ServiceAlert.route_id.in_(members),
            (ServiceAlert.end_time.is_(None)) | (ServiceAlert.end_time >= datetime.utcnow()),
        )
    )
    if active_alert:
        factors.append("active service alert")

    weather = db.scalar(select(WeatherObservation).order_by(WeatherObservation.observed_time.desc()).limit(1))
    if weather:
        if (weather.rain or 0) > 0 or (weather.precipitation or 0) > 0:
            factors.append("rain")
        if (weather.snow or 0) > 0:
            factors.append("snow")
        if (weather.wind_speed or 0) >= 35:
            factors.append("high wind")

    return factors[:4] or ["limited route history"]


def _model_features(db: Session, payload: PredictionRequest) -> pd.DataFrame:
    members = member_route_ids(db, payload.route_id)
    weather = db.scalar(select(WeatherObservation).order_by(WeatherObservation.observed_time.desc()).limit(1))
    route_avg = db.scalar(
        select(func.avg(RealtimeObservation.delay_minutes)).where(
            RealtimeObservation.route_id.in_(members),
            RealtimeObservation.source == LIVE_SOURCE,
        )
    ) or 0
    stop_avg = 0
    if payload.stop_id:
        stop_avg = db.scalar(
            select(func.avg(RealtimeObservation.delay_minutes)).where(
                RealtimeObservation.stop_id == payload.stop_id,
                RealtimeObservation.source == LIVE_SOURCE,
            )
        ) or 0
    recent_since = datetime.utcnow() - timedelta(minutes=30)
    recent_avg = db.scalar(
        select(func.avg(RealtimeObservation.delay_minutes)).where(
            RealtimeObservation.route_id.in_(members),
            RealtimeObservation.source == LIVE_SOURCE,
            RealtimeObservation.observed_time >= recent_since,
        )
    ) or route_avg

    return pd.DataFrame([
        {
            "route_id": payload.route_id,
            "stop_id": payload.stop_id or "",
            "hour": payload.datetime.hour,
            "minute": payload.datetime.minute,
            "day_of_week": payload.datetime.weekday(),
            "is_weekend": int(payload.datetime.weekday() >= 5),
            "is_rush_hour": int(is_rush_hour(payload.datetime)),
            "month": payload.datetime.month,
            "temperature": weather.temperature if weather else 0,
            "precipitation": weather.precipitation if weather else 0,
            "snow": weather.snow if weather else 0,
            "rain": weather.rain if weather else 0,
            "wind_speed": weather.wind_speed if weather else 0,
            "weather_main": weather.weather_main if weather else "",
            "historical_avg_delay_for_route": route_avg,
            "historical_avg_delay_for_stop": stop_avg,
            "recent_delay_avg_last_30_min": recent_avg,
        }
    ])


def predict_delay(db: Session, payload: PredictionRequest) -> PredictionResponse:
    probability, expected_minutes, sample_size, is_data_driven = estimate_baseline(
        db, payload.route_id, payload.datetime, payload.stop_id
    )
    model_used = False
    basis = "historical-baseline" if is_data_driven else "heuristic-default"

    # The trained model path is reserved for Phase 5. Baseline stays active until
    # enough observations exist and feature parity is available.
    if CLASSIFIER_PATH.exists() and REGRESSOR_PATH.exists() and sample_size >= 100:
        try:
            classifier = joblib.load(CLASSIFIER_PATH)
            regressor = joblib.load(REGRESSOR_PATH)
            features = _model_features(db, payload)
            probability = round(float(classifier.predict_proba(features)[0][1]), 2)
            expected_minutes = round(float(regressor.predict(features)[0]), 1)
            model_used = True
            basis = "ml-model"
        except Exception:
            model_used = False

    db.add(
        PredictionLog(
            route_id=payload.route_id,
            stop_id=payload.stop_id,
            requested_time=payload.datetime,
            predicted_delay_probability=probability,
            predicted_delay_minutes=expected_minutes,
            model_version="ml-v0" if model_used else "baseline-v0",
        )
    )
    db.commit()

    return PredictionResponse(
        delay_probability=probability,
        expected_delay_minutes=expected_minutes,
        delay_range=_range(expected_minutes),
        risk_label=risk_label(probability),
        confidence=_confidence(sample_size, model_used),
        basis=basis,
        is_data_driven=is_data_driven,
        sample_size=sample_size,
        top_factors=_top_factors(db, payload),
        live_status=get_live_status(db, payload.route_id, payload.stop_id),
    )
