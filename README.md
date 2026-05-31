# GOPredict

A web app focused exclusively on **GO Transit rail (train) delay prediction**. It collects GO Transit / Metrolinx GTFS schedule and realtime data, stores historical delay observations, and predicts delay risk by rail line, stop, and travel time. Bus service is intentionally out of scope (only GTFS `route_type == 2` rail lines are imported and served).

## Problem

GO Transit rail commuters need a practical signal before leaving: live delay status, predicted delay risk, route reliability, active alerts, and historical delay trends. This app uses GTFS static data, GTFS Realtime feeds, weather observations, and a baseline predictor that can be replaced by trained scikit-learn models once enough history is collected.

## Features

- **Live status vs predicted risk** — the prediction clearly separates the currently observed delay state (`live_status`) from the forecast delay risk, and flags heuristic estimates (`is_data_driven: false`) when there is not enough history.
- **Route reliability** — each rail line gets a 0-100 score plus a High/Medium/Low grade and plain-language reasons, derived from delay frequency, average delay length, cancellation rate, active alerts, and recent disruptions (`GET /reliability`).
- **Analytics** — delays by hour of day, delays by day of week, per-route snapshots, and a route-level reliability comparison.
- **Route snapshots** — current status, predicted risk, average recent delay, reliability score, recent alerts, and last-updated time per line (`GET /routes/snapshots`).
- **Resilient collection** — GTFS Realtime fetches use a short-lived cache, retry with backoff on rate limiting (HTTP 429) and upstream errors, and validate/clamp implausible delay values.

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

Do not put real API keys in `backend/.env.example`, frontend files, README files, or committed code. `backend/.env` is ignored by Git and is the only intended local place for secrets.

## Quick Start (one command)

On Windows, from the project root:

```powershell
.\run.ps1
```

This auto-creates the Python virtual environment, installs backend and frontend dependencies, creates `backend/.env` from the example, and launches both the API (`http://localhost:8000`) and the React app (`http://localhost:5173`) in separate windows. Re-running it skips setup steps that are already done. Add your API keys to `backend/.env` to enable realtime and weather collection.

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

Open Metrolinx GTFS Realtime is a live feed, not a historical archive. GOPredict builds historical delay charts by continuously collecting snapshots into the local database over time.

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
