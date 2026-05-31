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


class LiveStatus(BaseModel):
    """Currently observed delay state, kept separate from predicted risk."""

    status: str
    average_delay_minutes: float
    sample_size: int
    last_updated: datetime | None = None


class PredictionResponse(BaseModel):
    delay_probability: float
    expected_delay_minutes: float
    delay_range: str
    risk_label: str
    confidence: str
    # How the prediction was produced: "ml-model", "historical-baseline", or
    # "heuristic-default" (no history yet, not data-backed).
    basis: str
    is_data_driven: bool
    sample_size: int
    top_factors: list[str]
    live_status: LiveStatus
