from pathlib import Path

import pandas as pd

from app.database import engine


def build_training_dataset() -> pd.DataFrame:
    query = """
    SELECT
      ro.route_id,
      ro.stop_id,
      ro.observed_time,
      ro.delay_minutes,
      strftime('%H', ro.observed_time) AS hour,
      strftime('%M', ro.observed_time) AS minute,
      strftime('%w', ro.observed_time) AS day_of_week,
      strftime('%m', ro.observed_time) AS month,
      wo.temperature,
      wo.precipitation,
      wo.snow,
      wo.rain,
      wo.wind_speed,
      wo.weather_main
    FROM realtime_observations ro
    LEFT JOIN weather_observations wo
      ON wo.id = (
        SELECT id FROM weather_observations
        ORDER BY ABS(strftime('%s', observed_time) - strftime('%s', ro.observed_time))
        LIMIT 1
      )
    WHERE ro.delay_minutes IS NOT NULL
      AND ro.source = 'gtfs-realtime'
    """
    df = pd.read_sql_query(query, engine)
    if df.empty:
        return df
    df["hour"] = df["hour"].astype(int)
    df["minute"] = df["minute"].astype(int)
    df["day_of_week"] = df["day_of_week"].astype(int)
    df["month"] = df["month"].astype(int)
    df["is_weekend"] = df["day_of_week"].isin([0, 6]).astype(int)
    df["is_rush_hour"] = df["hour"].between(7, 9).astype(int) | df["hour"].between(16, 18).astype(int)
    df["is_delayed"] = (df["delay_minutes"] >= 5).astype(int)
    df["historical_avg_delay_for_route"] = df.groupby("route_id")["delay_minutes"].transform("mean")
    df["historical_avg_delay_for_stop"] = df.groupby("stop_id")["delay_minutes"].transform("mean")
    df["recent_delay_avg_last_30_min"] = df["historical_avg_delay_for_route"]
    return df


def main() -> None:
    df = build_training_dataset()
    Path("models").mkdir(exist_ok=True)
    output = Path("models/training_dataset.csv")
    df.to_csv(output, index=False)
    print(f"wrote {len(df)} rows to {output}")


if __name__ == "__main__":
    main()
