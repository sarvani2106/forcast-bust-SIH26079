import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix


# --------------------------------------------------
# 1. Load features
# --------------------------------------------------

df = pd.read_csv("data/processed/features.csv")

print("Dataset shape:", df.shape)


# --------------------------------------------------
# 2. Select ML features available at prediction time
# --------------------------------------------------

features = [
    "lead_day",
    "rainfall_forecast",
    "historical_error",
    "forecast_revision",
    "forecast_stability"
]

X = df[features]
y = df["bust"]


# --------------------------------------------------
# 3. Train / test split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y
)


print("\nTraining rows:", len(X_train))
print("Testing rows:", len(X_test))


# --------------------------------------------------
# 4. Create Random Forest
# --------------------------------------------------

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=5,
    random_state=42,
    class_weight="balanced"
)


# --------------------------------------------------
# 5. Train
# --------------------------------------------------

model.fit(X_train, y_train)

print("\nModel training complete!")


# --------------------------------------------------
# 6. Predictions
# --------------------------------------------------

y_pred = model.predict(X_test)


# --------------------------------------------------
# 7. Evaluation
# --------------------------------------------------

print("\n===== CLASSIFICATION REPORT =====")
print(classification_report(y_test, y_pred))


print("\n===== CONFUSION MATRIX =====")
print(confusion_matrix(y_test, y_pred))


# --------------------------------------------------
# 8. Feature importance
# --------------------------------------------------

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\n===== FEATURE IMPORTANCE =====")
print(importance)


# --------------------------------------------------
# 9. Bust probabilities
# --------------------------------------------------

probabilities = model.predict_proba(X_test)[:, 1]

print("\n===== SAMPLE BUST PROBABILITIES =====")

for probability in probabilities[:10]:
    print(f"Bust probability: {probability:.2%}")