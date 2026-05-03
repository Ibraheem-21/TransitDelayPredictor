from datetime import datetime, timedelta
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import PredictionLog, RealtimeObservation, ServiceAlert, WeatherObservation
from app.schemas import PredictionRequest, PredictionResponse

CLASSIFIER_PATH = Path("models/delay_classifier.pkl")
REGRESSOR_PATH = Path("models/delay_regressor.pkl")


def is_rush_hour(value: datetime) -> bool:
    minutes = value.hour * 60 + value.minute
    return (6 * 60 + 30 <= minutes <= 9 * 60 + 30) or (15 * 60 + 30 <= minutes <= 18 * 60 + 30)


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


def _baseline(db: Session, payload: PredictionRequest) -> tuple[float, float, int]:
    filters = [RealtimeObservation.route_id == payload.route_id]
    if payload.stop_id:
        filters.append(RealtimeObservation.stop_id == payload.stop_id)

    total = db.scalar(select(func.count()).select_from(RealtimeObservation).where(*filters)) or 0
    if total == 0:
        base_probability = 0.35 if is_rush_hour(payload.datetime) else 0.18
        base_minutes = 6.0 if is_rush_hour(payload.datetime) else 3.0
        return base_probability, base_minutes, 0

    delayed = db.scalar(select(func.count()).select_from(RealtimeObservation).where(*filters, RealtimeObservation.delay_minutes >= 5)) or 0
    avg_delay = db.scalar(select(func.avg(RealtimeObservation.delay_minutes)).where(*filters)) or 0
    probability = delayed / total

    if is_rush_hour(payload.datetime):
        probability = min(1, probability + 0.12)
        avg_delay = float(avg_delay) + 2

    weather = db.scalar(select(WeatherObservation).order_by(WeatherObservation.observed_time.desc()).limit(1))
    if weather:
        if (weather.rain or 0) > 0 or (weather.precipitation or 0) >= 1:
            probability = min(1, probability + 0.07)
            avg_delay = float(avg_delay) + 1
        if (weather.snow or 0) > 0:
            probability = min(1, probability + 0.12)
            avg_delay = float(avg_delay) + 2
        if (weather.wind_speed or 0) >= 35:
            probability = min(1, probability + 0.05)
            avg_delay = float(avg_delay) + 1

    return round(probability, 2), round(float(avg_delay), 1), total


def _top_factors(db: Session, payload: PredictionRequest) -> list[str]:
    factors: list[str] = []
    if is_rush_hour(payload.datetime):
        factors.append("rush hour")

    recent_since = datetime.utcnow() - timedelta(minutes=30)
    recent_avg = db.scalar(
        select(func.avg(RealtimeObservation.delay_minutes)).where(
            RealtimeObservation.route_id == payload.route_id,
            RealtimeObservation.observed_time >= recent_since,
        )
    )
    if recent_avg and recent_avg >= 5:
        factors.append("recent route delays")

    active_alert = db.scalar(
        select(func.count()).select_from(ServiceAlert).where(
            ServiceAlert.route_id == payload.route_id,
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
    weather = db.scalar(select(WeatherObservation).order_by(WeatherObservation.observed_time.desc()).limit(1))
    route_avg = db.scalar(
        select(func.avg(RealtimeObservation.delay_minutes)).where(RealtimeObservation.route_id == payload.route_id)
    ) or 0
    stop_avg = 0
    if payload.stop_id:
        stop_avg = db.scalar(
            select(func.avg(RealtimeObservation.delay_minutes)).where(RealtimeObservation.stop_id == payload.stop_id)
        ) or 0
    recent_since = datetime.utcnow() - timedelta(minutes=30)
    recent_avg = db.scalar(
        select(func.avg(RealtimeObservation.delay_minutes)).where(
            RealtimeObservation.route_id == payload.route_id,
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
    probability, expected_minutes, sample_size = _baseline(db, payload)
    model_used = False

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
        confidence=_confidence(sample_size, model_used),
        top_factors=_top_factors(db, payload),
    )
