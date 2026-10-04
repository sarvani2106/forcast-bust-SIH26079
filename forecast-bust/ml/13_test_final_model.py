import pandas as pd
import joblib

# --------------------------------------------------
# Load real dataset
# --------------------------------------------------

df = pd.read_csv(
    "data/processed/real_ml_dataset.csv"
)

features = [
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

# --------------------------------------------------
# Load FINAL calibrated model
# --------------------------------------------------

model = joblib.load(
    "models/calibrated_forecast_bust_model.pkl"
)

BUST_THRESHOLD = 0.30

# --------------------------------------------------
# Select a few real test cases
# --------------------------------------------------

test_df = df[
    df["forecast_date"] >= "2025-09-25"
].copy()

# Pick representative cases:
# low rainfall
# medium rainfall
# high rainfall

samples = pd.concat([
    test_df.nsmallest(1, "forecast_rainfall"),
    test_df.iloc[[len(test_df) // 2]],
    test_df.nlargest(1, "forecast_rainfall")
])

# --------------------------------------------------
# Predict
# --------------------------------------------------

X = samples[features]

probabilities = model.predict_proba(X)[:, 1]

print("=" * 80)
print("FINAL CALIBRATED MODEL TEST")
print("=" * 80)

for i, (_, row) in enumerate(samples.iterrows()):

    probability = probabilities[i]

    bust = probability >= BUST_THRESHOLD

    confidence = (
        1 - probability
        if not bust
        else probability
    )

    if probability < 0.30:
        risk = "LOW"
    elif probability < 0.60:
        risk = "MODERATE"
    else:
        risk = "HIGH"

    print("\n" + "-" * 80)

    print(f"Forecast Date       : {row['forecast_date']}")
    print(f"Latitude            : {row['LATITUDE']:.4f}")
    print(f"Longitude           : {row['LONGITUDE']:.4f}")
    print(f"Lead Day            : {int(row['lead_day'])}")

    print(
        f"Forecast Rainfall   : "
        f"{row['forecast_rainfall']:.2f} mm"
    )

    print(
        f"Previous Forecast   : "
        f"{row['previous_forecast']:.2f} mm"
    )

    print(
        f"Forecast Revision   : "
        f"{row['forecast_revision']:.2f} mm"
    )

    print(
        f"Historical MAE      : "
        f"{row['historical_mae']:.2f} mm"
    )

    print(
        f"\nBust Probability    : "
        f"{probability * 100:.2f}%"
    )

    print(
        f"Confidence          : "
        f"{confidence * 100:.2f}%"
    )

    print(f"Risk                : {risk}")
    print(
        f"Bust Prediction     : "
        f"{'BUST' if bust else 'NORMAL'}"
    )

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)