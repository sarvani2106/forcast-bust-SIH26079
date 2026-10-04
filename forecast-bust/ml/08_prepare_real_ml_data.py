import pandas as pd
import numpy as np
from pathlib import Path

INPUT = "data/processed/real_forecast_dataset_aug_sep.csv"
OUTPUT = "data/processed/real_ml_dataset.csv"

print("Loading real dataset...")

df = pd.read_csv(INPUT)

df["forecast_date"] = pd.to_datetime(df["forecast_date"])
df["date"] = pd.to_datetime(df["date"])

df = df.sort_values(
    ["LATITUDE", "LONGITUDE", "lead_day", "forecast_date"]
).reset_index(drop=True)

print("Original shape:", df.shape)

# --------------------------------------------------
# 1. Previous forecast
# --------------------------------------------------
# Previous forecast initialization for the same
# location and lead day.

df["previous_forecast"] = (
    df.groupby(
        ["LATITUDE", "LONGITUDE", "lead_day"]
    )["forecast_rainfall"]
    .shift(1)
)

# --------------------------------------------------
# 2. Forecast revision
# --------------------------------------------------

df["forecast_revision"] = (
    df["forecast_rainfall"]
    - df["previous_forecast"]
).abs()

# --------------------------------------------------
# 3. Forecast stability
# --------------------------------------------------

df["forecast_stability"] = (
    1 / (1 + df["forecast_revision"])
)

# --------------------------------------------------
# 4. Historical forecast error
# --------------------------------------------------
# IMPORTANT:
# Only previous forecasts are used.
# Current rainfall_error is NEVER included.

df["historical_mae"] = (
    df.groupby(
        ["LATITUDE", "LONGITUDE", "lead_day"]
    )["rainfall_error"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(
            window=5,
            min_periods=1
        )
        .mean()
    )
)

# --------------------------------------------------
# 5. Spatial / geographic features
# --------------------------------------------------

df["latitude_abs"] = df["LATITUDE"].abs()

df["longitude_abs"] = df["LONGITUDE"].abs()

# --------------------------------------------------
# 6. Forecast intensity features
# --------------------------------------------------

df["forecast_rainfall_squared"] = (
    df["forecast_rainfall"] ** 2
)

df["log_forecast_rainfall"] = np.log1p(
    df["forecast_rainfall"]
)

# --------------------------------------------------
# 7. Lead-time features
# --------------------------------------------------

df["lead_day_squared"] = (
    df["lead_day"] ** 2
)

# --------------------------------------------------
# 8. Remove rows where historical features
#    cannot be calculated
# --------------------------------------------------

df = df.dropna(
    subset=[
        "previous_forecast",
        "historical_mae"
    ]
)

# --------------------------------------------------
# 9. Define ML features
# --------------------------------------------------

feature_columns = [
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

target_column = "bust"

# --------------------------------------------------
# 10. Create final ML dataset
# --------------------------------------------------

ml_df = df[
    [
        "forecast_date",
        "date",
        *feature_columns,
        target_column
    ]
].copy()

# --------------------------------------------------
# 11. Leakage audit
# --------------------------------------------------

forbidden = [
    "actual_rainfall",
    "rainfall_error"
]

for column in forbidden:

    if column in ml_df.columns:
        raise RuntimeError(
            f"DATA LEAKAGE: {column} found in ML dataset!"
        )

print("\nLeakage audit: PASSED")

# --------------------------------------------------
# 12. Save
# --------------------------------------------------

Path("data/processed").mkdir(
    parents=True,
    exist_ok=True
)

ml_df.to_csv(
    OUTPUT,
    index=False
)

# --------------------------------------------------
# 13. Summary
# --------------------------------------------------

print("\n========================================")
print("REAL ML DATASET CREATED")
print("========================================")

print("Saved:", OUTPUT)
print("Shape:", ml_df.shape)

print("\nFeatures:")
for feature in feature_columns:
    print(" -", feature)

print("\nTarget:")
print(" - bust")

print("\nBust distribution:")
print(
    ml_df["bust"].value_counts()
)

print("\nBust rate:")
print(
    f"{ml_df['bust'].mean() * 100:.2f}%"
)

print("\nSample:")
print(
    ml_df.head()
)