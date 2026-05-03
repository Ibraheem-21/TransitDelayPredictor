import time
from datetime import datetime

from app.scripts.collect_alerts import main as collect_alerts
from app.scripts.collect_realtime import main as collect_realtime
from app.scripts.collect_weather import main as collect_weather


def main() -> None:
    last_alerts = 0.0
    last_weather = 0.0
    while True:
        now = time.time()
        print(f"[{datetime.utcnow().isoformat()}] collecting realtime")
        collect_realtime()
        if now - last_alerts >= 10 * 60:
            collect_alerts()
            last_alerts = now
        if now - last_weather >= 60 * 60:
            collect_weather()
            last_weather = now
        time.sleep(5 * 60)


if __name__ == "__main__":
    main()
