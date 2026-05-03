from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PredictionRequest, PredictionResponse
from app.services.prediction_service import predict_delay

router = APIRouter(prefix="/predict", tags=["predictions"])


@router.post("", response_model=PredictionResponse)
def predict(payload: PredictionRequest, db: Session = Depends(get_db)) -> PredictionResponse:
    return predict_delay(db, payload)
