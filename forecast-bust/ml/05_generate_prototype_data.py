import pandas as pd

# --------------------------------------------------
# 1. Load prototype dataset
# --------------------------------------------------

df = pd.read_csv(
    "data/processed/prototype_dataset.csv"
)

print("Original dataset:", df.shape)


# --------------------------------------------------
# 2. Convert weather regime into numerical features
# --------------------------------------------------

df = pd.get_dummies(
    df,
    columns=["weather_regime"],
    dtype=int
)


# --------------------------------------------------
# 3. Select ONLY information available
#    at forecast time
# --------------------------------------------------

features = [
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
    "weather_regime_Heat Wave"
]


X = df[features]

# Target
y = df["bust"]


# --------------------------------------------------
# 4. Combine features + target
# --------------------------------------------------

ml_data = X.copy()

ml_data["bust"] = y


# --------------------------------------------------
# 5. Save
# --------------------------------------------------

output_path = "data/processed/ml_dataset.csv"

ml_data.to_csv(
    output_path,
    index=False
)


# --------------------------------------------------
# 6. Display
# --------------------------------------------------

print("\n===== ML DATASET =====")

print("Features:")
for feature in features:
    print("-", feature)

print("\nTarget:")
print("- bust")

print("\nShape:", ml_data.shape)

print("\nBust distribution:")
print(ml_data["bust"].value_counts())

print("\nSaved to:")
print(output_path)