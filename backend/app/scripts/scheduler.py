import time
from datetime import datetime, UTC

from app.scripts.collect_alerts import main as collect_alerts
from app.scripts.collect_realtime import main as collect_realtime
from app.scripts.collect_weather import main as collect_weather


def main() -> None:
    last_alerts = 0.0
    last_weather = 0.0
    while True:
        now = time.time()
        print(f"[{datetime.now(UTC).isoformat()}] collecting realtime", flush=True)
        try:
            collect_realtime()
        except Exception as exc:
            print(f"realtime collection failed: {exc}", flush=True)
        if now - last_alerts >= 10 * 60:
            try:
                collect_alerts()
                last_alerts = now
            except Exception as exc:
                print(f"alerts collection failed: {exc}", flush=True)
        if now - last_weather >= 60 * 60:
            try:
                collect_weather()
                last_weather = now
            except Exception as exc:
                print(f"weather collection failed: {exc}", flush=True)
        time.sleep(5 * 60)


if __name__ == "__main__":
    main()
