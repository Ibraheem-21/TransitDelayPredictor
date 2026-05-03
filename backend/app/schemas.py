from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RouteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    route_id: str
    route_name: str
    route_type: str | None = None
    agency: str | None = None


class StopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stop_id: str
    stop_name: str
    latitude: float | None = None
    longitude: float | None = None


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    route_id: str | None = None
    stop_id: str | None = None
    alert_header: str | None = None
    alert_description: str | None = None
    cause: str | None = None
    effect: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class PredictionRequest(BaseModel):
    route_id: str
    stop_id: str | None = None
    datetime: datetime


class PredictionResponse(BaseModel):
    delay_probability: float
    expected_delay_minutes: float
    delay_range: str
    confidence: str
    top_factors: list[str]
