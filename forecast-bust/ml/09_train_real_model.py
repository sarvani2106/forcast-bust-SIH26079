import pandas as pd
import numpy as np
import joblib
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

INPUT = "data/processed/real_ml_dataset.csv"
MODEL_OUTPUT = "models/real_forecast_bust_model.pkl"

# --------------------------------------------------
# Load data
# --------------------------------------------------

print("Loading real ML dataset...")

df = pd.read_csv(INPUT)

df["forecast_date"] = pd.to_datetime(df["forecast_date"])

print("Dataset shape:", df.shape)

# --------------------------------------------------
# Define features
# --------------------------------------------------

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

TRAIN_END = "2025-09-24"

train = df[
    df["forecast_date"] <= TRAIN_END
].copy()

test = df[
    df["forecast_date"] > TRAIN_END
].copy()

print("\nTrain shape:", train.shape)
print("Test shape:", test.shape)

print(
    "\nTrain dates:",
    train["forecast_date"].min(),
    "to",
    train["forecast_date"].max()
)

print(
    "Test dates:",
    test["forecast_date"].min(),
    "to",
    test["forecast_date"].max()
)

# --------------------------------------------------
# Prepare X / y
# --------------------------------------------------

X_train = train[features]
y_train = train[target]

X_test = test[features]
y_test = test[target]

# --------------------------------------------------
# Check class distribution
# --------------------------------------------------

print("\nTraining target distribution:")
print(y_train.value_counts())

print("\nTesting target distribution:")
print(y_test.value_counts())

# --------------------------------------------------
# Train Random Forest
# --------------------------------------------------

print("\nTraining Random Forest...")

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_leaf=10,
    class_weight="balanced",
    n_jobs=-1,
    random_state=42
)

model.fit(X_train, y_train)

print("Training complete.")

# --------------------------------------------------
# Predictions
# --------------------------------------------------

y_pred = model.predict(X_test)

y_probability = model.predict_proba(X_test)[:, 1]

# --------------------------------------------------
# Metrics
# --------------------------------------------------

accuracy = accuracy_score(
    y_test,
    y_pred
)

precision = precision_score(
    y_test,
    y_pred,
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    y_probability
)

cm = confusion_matrix(
    y_test,
    y_pred
)

# --------------------------------------------------
# Print results
# --------------------------------------------------

print("\n========================================")
print("REAL MODEL RESULTS")
print("========================================")

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")
print(f"ROC-AUC  : {roc_auc:.4f}")

print("\nConfusion Matrix:")
print(cm)

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=["Normal", "Bust"],
        zero_division=0
    )
)

# --------------------------------------------------
# Feature importance
# --------------------------------------------------

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\nFeature Importance:")

for _, row in importance.iterrows():
    print(
        f"{row['feature']:<30} "
        f"{row['importance']:.6f}"
    )

# --------------------------------------------------
# Save model
# --------------------------------------------------

Path("models").mkdir(
    parents=True,
    exist_ok=True
)

joblib.dump(
    model,
    MODEL_OUTPUT
)

print("\nModel saved:")
print(MODEL_OUTPUT)