import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score
)

# --------------------------------------------------
# 1. Load ML dataset
# --------------------------------------------------

df = pd.read_csv("data/processed/ml_dataset.csv")

print("Dataset shape:", df.shape)


# --------------------------------------------------
# 2. Separate features and target
# --------------------------------------------------

X = df.drop(columns=["bust"])
y = df["bust"]


# --------------------------------------------------
# 3. Train / test split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining rows:", len(X_train))
print("Testing rows:", len(X_test))


# --------------------------------------------------
# 4. Random Forest
# --------------------------------------------------

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    min_samples_leaf=5,
    class_weight="balanced",
    random_state=42
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

y_probability = model.predict_proba(X_test)[:, 1]


# --------------------------------------------------
# 7. Evaluation
# --------------------------------------------------

print("\n===== CLASSIFICATION REPORT =====")

print(
    classification_report(
        y_test,
        y_pred,
        target_names=["Normal", "Bust"]
    )
)


print("\n===== CONFUSION MATRIX =====")

print(
    confusion_matrix(
        y_test,
        y_pred
    )
)


print("\n===== ROC-AUC =====")

print(
    f"{roc_auc_score(y_test, y_probability):.4f}"
)


# --------------------------------------------------
# 8. Feature importance
# --------------------------------------------------

importance = pd.DataFrame({
    "feature": X.columns,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\n===== FEATURE IMPORTANCE =====")

print(importance.to_string(index=False))


# --------------------------------------------------
# 9. Save model
# --------------------------------------------------

joblib.dump(
    model,
    "models/forecast_bust_model.pkl"
)

print("\nModel saved to:")
print("models/forecast_bust_model.pkl")


# --------------------------------------------------
# 10. Show sample predictions
# --------------------------------------------------

print("\n===== SAMPLE PREDICTIONS =====")

for i in range(10):

    probability = y_probability[i]

    print(
        f"Prediction {i+1}: "
        f"Bust Probability = {probability:.2%}"
    )