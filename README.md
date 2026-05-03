# GOPredict

A web app for collecting GO Transit GTFS schedule and realtime data, storing historical delay observations, and predicting delay risk by route, stop, and travel time.

## Problem

GO Transit commuters need a practical signal before leaving: delay probability, expected delay range, route reliability, active alerts, and historical delay trends. This MVP uses GTFS static data, GTFS Realtime feeds, OpenWeather observations, and a baseline predictor that can be replaced by trained scikit-learn models once enough history is collected.

## Data Sources

- Metrolinx / GO Transit GTFS static schedule zip
- GTFS Realtime trip updates and service alerts
- OpenWeather current weather API

## Environment

Copy `backend/.env.example` to `backend/.env` and fill in:

```env
DATABASE_URL=sqlite:///./go_delay_predictor.db
OPENWEATHER_API_KEY=
WORLDWEATHERONLINE_API_KEY=
OPENMETROLINX_API_KEY=
GTFS_STATIC_URL=https://assets.metrolinx.com/raw/upload/Documents/Metrolinx/Open%20Data/GO-GTFS.zip
GTFS_REALTIME_TRIP_UPDATES_URL=https://api.openmetrolinx.com/OpenDataAPI/api/V1/Gtfs/Feed/TripUpdates
GTFS_REALTIME_ALERTS_URL=https://api.openmetrolinx.com/OpenDataAPI/api/V1/Gtfs/Feed/Alerts
```

SQLite is the local default. PostgreSQL can be used by setting `DATABASE_URL` to a PostgreSQL SQLAlchemy URL.

Open Metrolinx realtime API access is free, but it requires registration for an access key. Put that key in `OPENMETROLINX_API_KEY`.

Weather collection prefers `WORLDWEATHERONLINE_API_KEY` when present and falls back to `OPENWEATHER_API_KEY`. The default 10-city hourly collection uses about 240 requests/day.

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs on `http://localhost:8000`.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The React app runs on `http://localhost:5173`.

## Import GTFS Data

```bash
cd backend
python -m app.scripts.import_gtfs_static
```

This downloads the configured GTFS static zip, extracts `routes.txt`, `stops.txt`, `trips.txt`, and `stop_times.txt`, then loads them into the database.

## Collect Realtime Data

```bash
cd backend
python -m app.scripts.collect_realtime
python -m app.scripts.collect_alerts
python -m app.scripts.collect_weather
```

For the MVP scheduler loop:

```bash
cd backend
python -m app.scripts.scheduler
```

## Temporary Demo Data

If you are waiting for an Open Metrolinx API key, seed synthetic observations generated from the real imported GTFS schedule:

```bash
cd backend
python -m app.scripts.seed_demo_observations
```

These rows are marked with `source=synthetic`. They are useful for UI development, charts, and baseline predictor testing, but they are not live Metrolinx delay observations.

## Model Explanation

The MVP prediction endpoint uses a baseline predictor until enough realtime observations exist. The baseline estimates delay probability from the historical percentage of trips delayed by at least 5 minutes for the selected route and stop, with a rush-hour adjustment.

Once at least 50 observations exist, run:

```bash
cd backend
python -m app.ml.train_model
```

The trainer builds a dataset with route, stop, time, weather, and historical delay features, then trains a random forest classifier and random forest regressor.

## Screenshots

Add screenshots after loading route data and running the frontend.

## Future Improvements

- Map view of delayed routes
- Saved commutes
- Email or text alerts
- Compare departure times
- Station reliability rankings
- LLM-generated prediction explanations
