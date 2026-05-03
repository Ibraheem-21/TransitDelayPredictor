from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer

from app.ml.build_training_dataset import build_training_dataset


def main() -> None:
    df = build_training_dataset()
    if len(df) < 50:
        print("Not enough observations to train. Baseline predictor will be used.")
        return

    features = [
        "route_id",
        "stop_id",
        "hour",
        "minute",
        "day_of_week",
        "is_weekend",
        "is_rush_hour",
        "month",
        "temperature",
        "precipitation",
        "snow",
        "rain",
        "wind_speed",
        "weather_main",
        "historical_avg_delay_for_route",
        "historical_avg_delay_for_stop",
        "recent_delay_avg_last_30_min",
    ]
    X = df[features].fillna(0)
    y_class = df["is_delayed"]
    y_reg = df["delay_minutes"].clip(lower=0)

    categorical = ["route_id", "stop_id", "weather_main"]
    numeric = [column for column in features if column not in categorical]
    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ("num", "passthrough", numeric),
    ])

    X_train, X_test, yc_train, yc_test, yr_train, yr_test = train_test_split(
        X, y_class, y_reg, test_size=0.2, random_state=42
    )

    logistic = Pipeline([("pre", preprocessor), ("model", LogisticRegression(max_iter=1000))])
    forest_classifier = Pipeline([("pre", preprocessor), ("model", RandomForestClassifier(n_estimators=150, random_state=42))])
    regressor = Pipeline([("pre", preprocessor), ("model", RandomForestRegressor(n_estimators=150, random_state=42))])

    logistic.fit(X_train, yc_train)
    forest_classifier.fit(X_train, yc_train)
    regressor.fit(X_train, yr_train)

    predictions = forest_classifier.predict(X_test)
    delay_predictions = regressor.predict(X_test)

    print("logistic_accuracy", round(accuracy_score(yc_test, logistic.predict(X_test)), 3))
    print("accuracy", round(accuracy_score(yc_test, predictions), 3))
    print("precision", round(precision_score(yc_test, predictions, zero_division=0), 3))
    print("recall", round(recall_score(yc_test, predictions, zero_division=0), 3))
    print("f1", round(f1_score(yc_test, predictions, zero_division=0), 3))
    print("mae", round(mean_absolute_error(yr_test, delay_predictions), 3))

    Path("models").mkdir(exist_ok=True)
    joblib.dump(forest_classifier, "models/delay_classifier.pkl")
    joblib.dump(regressor, "models/delay_regressor.pkl")


if __name__ == "__main__":
    main()
