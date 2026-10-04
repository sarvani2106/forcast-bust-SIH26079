import os
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "calibrated_forecast_bust_model.pkl"
)

model = joblib.load(MODEL_PATH)

BUST_THRESHOLD = 0.30

FEATURES = [
    "lead_day",
    "lead_day_squared",
    "LATITUDE",
    "LONGITUDE",
    "latitude_abs",
    "longitude_abs",
    "forecast_rainfall",
    "forecast_rainfall_squared",
    "log_forecast_rainfall",
    "previous_forecast",
    "forecast_revision",
    "forecast_stability",
    "historical_mae"
]


def predict_real(row):

    model_input = pd.DataFrame(
        [[row[feature] for feature in FEATURES]],
        columns=FEATURES
    )

    probability = float(
        model.predict_proba(model_input)[0][1]
    )

    bust = probability >= BUST_THRESHOLD

    if probability >= 0.60:
        risk = "HIGH"
    elif probability >= BUST_THRESHOLD:
        risk = "MODERATE"
    else:
        risk = "LOW"

    confidence = (
        probability if bust
        else 1 - probability
    )

    return {
        "bust_probability": round(probability, 4),
        "confidence": round(confidence, 4),
        "risk": risk,
        "bust_prediction": "BUST" if bust else "NORMAL"
    }