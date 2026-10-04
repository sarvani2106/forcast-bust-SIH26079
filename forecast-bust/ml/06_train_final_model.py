"""Train and evaluate the production forecast-bust model.

The holdout is chronological because forecast records have meaningful dates.
Only features known when the forecast is issued are used for prediction.
"""

from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "prototype_dataset.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "forecast_bust_model.pkl"
METRICS_PATH = PROJECT_ROOT / "models" / "forecast_bust_model_metrics.json"

FEATURES = [
    "lead_day",
    "rainfall_forecast",
    "previous_forecast",
    "historical_mae",
    "weather_variability",
    "forecast_revision",
    "forecast_stability",
    "weather_regime_Normal",
    "weather_regime_Heavy Rain",
    "weather_regime_Monsoon",
    "weather_regime_Cyclonic",
    "weather_regime_Heat Wave",
]


def metrics_for(model, x_test, y_test):
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    matrix = confusion_matrix(y_test, predictions, labels=[0, 1])
    return {
        "accuracy": round(accuracy_score(y_test, predictions), 4),
        "precision": round(
            precision_score(y_test, predictions, zero_division=0), 4
        ),
        "recall": round(recall_score(y_test, predictions, zero_division=0), 4),
        "f1": round(f1_score(y_test, predictions, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, probabilities), 4),
        "confusion_matrix": matrix.tolist(),
    }


def build_model():
    return RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=3,
        class_weight="balanced",
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
    )


def main():
    data = pd.read_csv(DATA_PATH, parse_dates=["date"])
    data = pd.get_dummies(data, columns=["weather_regime"], dtype=int)
    missing = sorted(set(FEATURES) - set(data.columns))
    if missing:
        raise ValueError(f"Missing forecast-time features: {missing}")

    data = data.sort_values("date").reset_index(drop=True)
    x = data[FEATURES]
    y = data["bust"]
    split_at = int(len(data) * 0.8)
    x_train, x_test = x.iloc[:split_at], x.iloc[split_at:]
    y_train, y_test = y.iloc[:split_at], y.iloc[split_at:]

    existing = joblib.load(MODEL_PATH)
    existing_metrics = metrics_for(existing, x_test, y_test)

    candidate = build_model()
    candidate.fit(x_train, y_train)
    candidate_metrics = metrics_for(candidate, x_test, y_test)

    # F1 is the primary selection metric for the imbalanced bust class.
    if candidate_metrics["f1"] >= existing_metrics["f1"]:
        selected = candidate
        selected_metrics = candidate_metrics
        selected_name = "candidate"
    else:
        selected = existing
        selected_metrics = existing_metrics
        selected_name = "existing"

    # Fit the selected configuration on all rows before persisting it.
    if selected_name == "candidate":
        selected.fit(x, y)
        joblib.dump(selected, MODEL_PATH)

    report = {
        "validation": "chronological 80/20 holdout",
        "feature_columns": FEATURES,
        "class_distribution": {
            str(int(label)): int(count)
            for label, count in y.value_counts().sort_index().items()
        },
        "existing_model": existing_metrics,
        "candidate_model": candidate_metrics,
        "selected_model": selected_name,
        "selected_metrics": selected_metrics,
        "leakage_excluded": [
            "rainfall_actual",
            "rainfall_error",
            "bust",
        ],
    }
    METRICS_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Existing:", existing_metrics)
    print("Candidate:", candidate_metrics)
    print("Selected:", selected_name)
    print(f"Model saved to {MODEL_PATH}")
    print(f"Metrics saved to {METRICS_PATH}")


if __name__ == "__main__":
    main()
