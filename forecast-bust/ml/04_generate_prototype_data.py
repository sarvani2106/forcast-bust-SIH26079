import pandas as pd
import numpy as np

# Reproducible results
np.random.seed(42)

# --------------------------------------------------
# 1. Prototype regions
# --------------------------------------------------

regions = [
    "Coastal Andhra",
    "Odisha",
    "Telangana",
    "Tamil Nadu",
    "Rajasthan",
    "Maharashtra",
    "West Bengal",
    "Karnataka"
]

n_rows = 5000

# --------------------------------------------------
# 2. Basic forecast information
# --------------------------------------------------

df = pd.DataFrame({
    "region": np.random.choice(regions, n_rows),
    "date": pd.date_range(
        start="2024-01-01",
        periods=n_rows,
        freq="6h"
    ),
    "lead_day": np.random.randint(1, 11, n_rows)
})

# --------------------------------------------------
# 3. Weather regime
# --------------------------------------------------

regimes = [
    "Normal",
    "Heavy Rain",
    "Monsoon",
    "Cyclonic",
    "Heat Wave"
]

df["weather_regime"] = np.random.choice(
    regimes,
    n_rows,
    p=[0.45, 0.20, 0.20, 0.05, 0.10]
)

# --------------------------------------------------
# 4. Weather variability
# --------------------------------------------------

df["weather_variability"] = np.random.uniform(
    0.1, 1.0, n_rows
)

# --------------------------------------------------
# 5. Historical forecast error
# --------------------------------------------------

df["historical_mae"] = np.random.gamma(
    shape=2.0,
    scale=5.0,
    size=n_rows
)

# --------------------------------------------------
# 6. Forecast rainfall
# --------------------------------------------------

df["rainfall_forecast"] = np.random.gamma(
    shape=2.5,
    scale=20,
    size=n_rows
)

# --------------------------------------------------
# 7. Previous forecast
# --------------------------------------------------

revision_factor = np.random.normal(
    loc=0,
    scale=0.25,
    size=n_rows
)

df["previous_forecast"] = (
    df["rainfall_forecast"] *
    (1 + revision_factor)
).clip(lower=0)

# --------------------------------------------------
# 8. Forecast revision
# --------------------------------------------------

df["forecast_revision"] = (
    df["rainfall_forecast"] -
    df["previous_forecast"]
).abs()

# --------------------------------------------------
# 9. Forecast stability
# --------------------------------------------------

df["forecast_stability"] = (
    1 / (1 + df["forecast_revision"])
)

# --------------------------------------------------
# 10. Simulate actual rainfall
# --------------------------------------------------

# Base error increases with lead time,
# historical error and weather variability.

base_error = (
    2
    + df["lead_day"] * 1.5
    + df["historical_mae"] * 0.5
    + df["weather_variability"] * 12
)

# Certain weather regimes are harder to forecast

regime_multiplier = df["weather_regime"].map({
    "Normal": 1.0,
    "Heavy Rain": 1.4,
    "Monsoon": 1.3,
    "Cyclonic": 1.7,
    "Heat Wave": 1.2
})

error = (
    np.random.normal(0, 1, n_rows)
    * base_error
    * regime_multiplier
)

df["rainfall_actual"] = (
    df["rainfall_forecast"] - error
).clip(lower=0)

# --------------------------------------------------
# 11. Actual forecast error
# --------------------------------------------------

df["rainfall_error"] = (
    df["rainfall_forecast"] -
    df["rainfall_actual"]
).abs()

# --------------------------------------------------
# 12. Define forecast bust
# --------------------------------------------------

# Prototype rule:
# Bust when error is significantly larger
# than the expected historical error.

threshold = (
    df["historical_mae"] * 2
    + 15
)

df["bust"] = (
    df["rainfall_error"] >= threshold
).astype(int)

# --------------------------------------------------
# 13. Save
# --------------------------------------------------

output_path = "data/processed/prototype_dataset.csv"

df.to_csv(output_path, index=False)

# --------------------------------------------------
# 14. Summary
# --------------------------------------------------

print("===== PROTOTYPE DATA GENERATED =====")

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nRegions:")
print(df["region"].value_counts())

print("\nLead days:")
print(df["lead_day"].value_counts().sort_index())

print("\nWeather regimes:")
print(df["weather_regime"].value_counts())

print("\nBust distribution:")
print(df["bust"].value_counts())

print("\nBust percentage:")
print(f"{df['bust'].mean() * 100:.2f}%")

print("\nSaved to:")
print(output_path)