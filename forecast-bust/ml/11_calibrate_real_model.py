import pandas as pd
import joblib
import numpy as np
from sklearn.frozen import FrozenEstimator

from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    brier_score_loss,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score
)

# --------------------------------------------------
# Load dataset
# --------------------------------------------------

df = pd.read_csv("data/processed/real_ml_dataset.csv")

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

target = "bust"

# --------------------------------------------------
# Chronological split
# --------------------------------------------------

train_df = df[df["forecast_date"] <= "2025-09-24"].copy()
test_df = df[df["forecast_date"] >= "2025-09-25"].copy()

# Use last 20% of training period for calibration
train_dates = sorted(train_df["forecast_date"].unique())

split_index = int(len(train_dates) * 0.8)

fit_dates = train_dates[:split_index]
calibration_dates = train_dates[split_index:]

fit_df = train_df[train_df["forecast_date"].isin(fit_dates)]
cal_df = train_df[train_df["forecast_date"].isin(calibration_dates)]

X_fit = fit_df[features]
y_fit = fit_df[target]

X_cal = cal_df[features]
y_cal = cal_df[target]

X_test = test_df[features]
y_test = test_df[target]

print("=" * 70)
print("CALIBRATION DATA")
print("=" * 70)

print(f"Model fit dates       : {fit_dates[0]} → {fit_dates[-1]}")
print(f"Calibration dates     : {calibration_dates[0]} → {calibration_dates[-1]}")
print(f"Final test dates      : {test_df['forecast_date'].min()} → {test_df['forecast_date'].max()}")

print(f"\nFit rows              : {len(X_fit):,}")
print(f"Calibration rows      : {len(X_cal):,}")
print(f"Test rows             : {len(X_test):,}")

# --------------------------------------------------
# Load existing model
# --------------------------------------------------

base_model = joblib.load(
    "models/real_forecast_bust_model.pkl"
)

# --------------------------------------------------
# Fit calibration model
# --------------------------------------------------

print("\nFitting probability calibration...")

from sklearn.frozen import FrozenEstimator

calibrated_model = CalibratedClassifierCV(
    FrozenEstimator(base_model),
    method="isotonic"
)

calibrated_model.fit(X_cal, y_cal)

# --------------------------------------------------
# Predictions
# --------------------------------------------------

raw_prob = base_model.predict_proba(X_test)[:, 1]

calibrated_prob = calibrated_model.predict_proba(X_test)[:, 1]

# --------------------------------------------------
# Brier scores
# --------------------------------------------------

raw_brier = brier_score_loss(y_test, raw_prob)
calibrated_brier = brier_score_loss(y_test, calibrated_prob)

print("\n" + "=" * 70)
print("CALIBRATION RESULTS")
print("=" * 70)

print(f"Raw Brier score        : {raw_brier:.5f}")
print(f"Calibrated Brier score : {calibrated_brier:.5f}")

if calibrated_brier < raw_brier:
    print("\n✓ Calibration improved probability quality.")
else:
    print("\n⚠ Calibration did not improve the Brier score.")

# --------------------------------------------------
# ROC-AUC
# --------------------------------------------------

print(f"\nRaw ROC-AUC             : {roc_auc_score(y_test, raw_prob):.4f}")
print(
    f"Calibrated ROC-AUC      : "
    f"{roc_auc_score(y_test, calibrated_prob):.4f}"
)

# --------------------------------------------------
# Threshold = 0.70
# --------------------------------------------------

threshold = 0.70

raw_pred = (raw_prob >= threshold).astype(int)
calibrated_pred = (calibrated_prob >= threshold).astype(int)

print("\n" + "=" * 70)
print("THRESHOLD 0.70")
print("=" * 70)

print("\nRAW MODEL")
print(f"Precision : {precision_score(y_test, raw_pred):.4f}")
print(f"Recall    : {recall_score(y_test, raw_pred):.4f}")
print(f"F1        : {f1_score(y_test, raw_pred):.4f}")

print("\nCALIBRATED MODEL")
print(f"Precision : {precision_score(y_test, calibrated_pred):.4f}")
print(f"Recall    : {recall_score(y_test, calibrated_pred):.4f}")
print(f"F1        : {f1_score(y_test, calibrated_pred):.4f}")

# --------------------------------------------------
# Save calibrated model
# --------------------------------------------------

joblib.dump(
    calibrated_model,
    "models/calibrated_forecast_bust_model.pkl"
)

print("\n✓ Saved:")
print("models/calibrated_forecast_bust_model.pkl")

# --------------------------------------------------
# Probability distribution comparison
# --------------------------------------------------

print("\n" + "=" * 70)
print("PROBABILITY DISTRIBUTION")
print("=" * 70)

print(
    f"Raw probability range        : "
    f"{raw_prob.min():.4f} → {raw_prob.max():.4f}"
)

print(
    f"Calibrated probability range : "
    f"{calibrated_prob.min():.4f} → {calibrated_prob.max():.4f}"
)

print("\nDone.")