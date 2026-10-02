import pandas as pd
import joblib

# --------------------------------------------------
# 1. Load model
# --------------------------------------------------

model = joblib.load(
    "models/forecast_bust_model.pkl"
)

# --------------------------------------------------
# 2. Load dataset
# --------------------------------------------------

df = pd.read_csv(
    "data/processed/prototype_dataset.csv"
)

# --------------------------------------------------
# 3. Select one example
# --------------------------------------------------

region = "Coastal Andhra"
lead_day = 5

row = df[
    (df["region"] == region) &
    (df["lead_day"] == lead_day)
].iloc[0]


# --------------------------------------------------
# 4. Create model input
# --------------------------------------------------

weather_regime = row["weather_regime"]

input_data = pd.DataFrame([{
    "lead_day": row["lead_day"],
    "rainfall_forecast": row["rainfall_forecast"],
    "previous_forecast": row["previous_forecast"],
    "historical_mae": row["historical_mae"],
    "weather_variability": row["weather_variability"],
    "forecast_revision": row["forecast_revision"],
    "forecast_stability": row["forecast_stability"],

    "weather_regime_Normal":
        int(weather_regime == "Normal"),

    "weather_regime_Heavy Rain":
        int(weather_regime == "Heavy Rain"),

    "weather_regime_Monsoon":
        int(weather_regime == "Monsoon"),

    "weather_regime_Cyclonic":
        int(weather_regime == "Cyclonic"),

    "weather_regime_Heat Wave":
        int(weather_regime == "Heat Wave")
}])


# --------------------------------------------------
# 5. Predict
# --------------------------------------------------

bust_probability = model.predict_proba(
    input_data
)[0][1]

confidence = 1 - bust_probability


# --------------------------------------------------
# 6. Risk classification
# --------------------------------------------------

if bust_probability >= 0.60:
    risk = "HIGH"
elif bust_probability >= 0.30:
    risk = "MODERATE"
else:
    risk = "LOW"


# --------------------------------------------------
# 7. Display
# --------------------------------------------------

print("\n===================================")
print("      FORECAST RELIABILITY")
print("===================================")

print(f"Region:             {region}")
print(f"Lead Day:           Day {lead_day}")

print("-----------------------------------")

print(
    f"Rainfall Forecast:  "
    f"{row['rainfall_forecast']:.1f} mm"
)

print(
    f"Previous Forecast:  "
    f"{row['previous_forecast']:.1f} mm"
)

print(
    f"Forecast Revision:  "
    f"{row['forecast_revision']:.1f} mm"
)

print(
    f"Historical MAE:     "
    f"{row['historical_mae']:.1f}"
)

print("-----------------------------------")

print(
    f"Bust Probability:   "
    f"{bust_probability:.2%}"
)

print(
    f"Confidence:         "
    f"{confidence:.2%}"
)

print(
    f"Risk:               "
    f"{risk}"
)

print(
    f"Stability Index:    "
    f"{row['forecast_stability']:.3f}"
)

print("===================================")