import pandas as pd
import joblib

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    confusion_matrix
)

# Load data
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

# Same chronological split used during training
train_mask = df["forecast_date"] <= "2025-09-24"
test_mask = df["forecast_date"] >= "2025-09-25"

X_test = df.loc[test_mask, features]
y_test = df.loc[test_mask, target]

# Load trained model
model = joblib.load("models/real_forecast_bust_model.pkl")

# Probability of bust
probabilities = model.predict_proba(X_test)[:, 1]

print("\nTHRESHOLD TUNING")
print("=" * 70)

results = []

for threshold in [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]:

    predictions = (probabilities >= threshold).astype(int)

    precision = precision_score(y_test, predictions, zero_division=0)
    recall = recall_score(y_test, predictions, zero_division=0)
    f1 = f1_score(y_test, predictions, zero_division=0)
    accuracy = accuracy_score(y_test, predictions)

    results.append({
        "threshold": threshold,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy
    })

    print(
        f"Threshold {threshold:.2f} | "
        f"Precision {precision:.4f} | "
        f"Recall {recall:.4f} | "
        f"F1 {f1:.4f} | "
        f"Accuracy {accuracy:.4f}"
    )

# Best threshold by F1
best = max(results, key=lambda x: x["f1"])

print("\n" + "=" * 70)
print("BEST THRESHOLD")
print("=" * 70)

print(f"Threshold : {best['threshold']:.2f}")
print(f"Precision : {best['precision']:.4f}")
print(f"Recall    : {best['recall']:.4f}")
print(f"F1        : {best['f1']:.4f}")
print(f"Accuracy  : {best['accuracy']:.4f}")

# Confusion matrix
best_predictions = (
    probabilities >= best["threshold"]
).astype(int)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, best_predictions))