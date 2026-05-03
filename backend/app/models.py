from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    route_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    route_name: Mapped[str] = mapped_column(String, index=True)
    route_type: Mapped[str | None] = mapped_column(String, nullable=True)
    agency: Mapped[str | None] = mapped_column(String, nullable=True)


class Stop(Base):
    __tablename__ = "stops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stop_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    stop_name: Mapped[str] = mapped_column(String, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trip_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    route_id: Mapped[str] = mapped_column(String, index=True)
    service_id: Mapped[str | None] = mapped_column(String, nullable=True)
    direction_id: Mapped[str | None] = mapped_column(String, nullable=True)
    trip_headsign: Mapped[str | None] = mapped_column(String, nullable=True)


class ScheduledStopTime(Base):
    __tablename__ = "scheduled_stop_times"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trip_id: Mapped[str] = mapped_column(String, index=True)
    stop_id: Mapped[str] = mapped_column(String, index=True)
    scheduled_arrival: Mapped[str | None] = mapped_column(String, nullable=True)
    scheduled_departure: Mapped[str | None] = mapped_column(String, nullable=True)
    stop_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)


class RealtimeObservation(Base):
    __tablename__ = "realtime_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trip_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    route_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    stop_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    observed_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    scheduled_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delay_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delay_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ServiceAlert(Base):
    __tablename__ = "service_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    route_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    stop_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    alert_header: Mapped[str | None] = mapped_column(String, nullable=True)
    alert_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cause: Mapped[str | None] = mapped_column(String, nullable=True)
    effect: Mapped[str | None] = mapped_column(String, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    station_or_city: Mapped[str] = mapped_column(String, index=True)
    observed_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    precipitation: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    snow: Mapped[float | None] = mapped_column(Float, nullable=True)
    rain: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_main: Mapped[str | None] = mapped_column(String, nullable=True)
    weather_description: Mapped[str | None] = mapped_column(String, nullable=True)


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    route_id: Mapped[str] = mapped_column(String, index=True)
    stop_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    requested_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    predicted_delay_probability: Mapped[float] = mapped_column(Float)
    predicted_delay_minutes: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
