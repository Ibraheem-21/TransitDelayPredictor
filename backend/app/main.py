from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, delays, predictions, routes, stops
from app.database import init_db

app = FastAPI(title="GOPredict", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(routes.router)
app.include_router(stops.router)
app.include_router(delays.router)
app.include_router(predictions.router)
app.include_router(alerts.router)
