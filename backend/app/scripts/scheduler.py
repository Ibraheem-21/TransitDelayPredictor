import time
from datetime import UTC, datetime

from app.scripts.collect_alerts import main as collect_alerts
from app.scripts.collect_realtime import main as collect_realtime
from app.scripts.collect_weather import main as collect_weather

BASE_INTERVAL_SECONDS = 5 * 60
ALERTS_INTERVAL_SECONDS = 10 * 60
WEATHER_INTERVAL_SECONDS = 60 * 60
MAX_BACKOFF_SECONDS = 30 * 60


def _run(label: str, fn) -> bool:
    try:
        fn()
        return True
    except Exception as exc:  # noqa: BLE001 - collector loop must stay alive
        print(f"{label} collection failed: {exc}", flush=True)
        return False


def main() -> None:
    last_alerts = 0.0
    last_weather = 0.0
    consecutive_failures = 0
    while True:
        now = time.time()
        print(f"[{datetime.now(UTC).isoformat()}] collecting realtime", flush=True)
        ok = _run("realtime", collect_realtime)
        if now - last_alerts >= ALERTS_INTERVAL_SECONDS:
            if _run("alerts", collect_alerts):
                last_alerts = now
        if now - last_weather >= WEATHER_INTERVAL_SECONDS:
            if _run("weather", collect_weather):
                last_weather = now

        # Exponential backoff protects the API budget when calls keep failing
        # (e.g. rate limiting or an outage); reset once a cycle succeeds.
        if ok:
            consecutive_failures = 0
            sleep_seconds = BASE_INTERVAL_SECONDS
        else:
            consecutive_failures += 1
            sleep_seconds = min(BASE_INTERVAL_SECONDS * (2**consecutive_failures), MAX_BACKOFF_SECONDS)
            print(f"backing off for {sleep_seconds}s after {consecutive_failures} failure(s)", flush=True)
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
