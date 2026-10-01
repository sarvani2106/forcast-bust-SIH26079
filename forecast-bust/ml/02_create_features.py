import pandas as pd

# Load verified forecast data
df = pd.read_csv("data/processed/forecast_errors.csv")

# Make sure data is correctly ordered
df["date"] = pd.to_datetime(df["date"])

df = df.sort_values(
    ["region", "date", "lead_day"]
).reset_index(drop=True)


# --------------------------------------------------
# 1. Historical forecast error
# --------------------------------------------------

# Use ONLY previous forecast errors.
# The current row must not be included.

df["historical_error"] = (
    df.groupby("region")["rainfall_error"]
      .transform(
          lambda x: x.shift(1)
                    .rolling(3, min_periods=1)
                    .mean()
      )
)


# --------------------------------------------------
# 2. Forecast revision
# --------------------------------------------------

# Difference between consecutive forecast values

df["forecast_revision"] = (
    df.groupby(["region", "lead_day"])["rainfall_forecast"]
      .diff()
      .abs()
)


# --------------------------------------------------
# 3. Forecast stability
# --------------------------------------------------

# Higher revision = less stable forecast

df["forecast_stability"] = (
    1 / (1 + df["forecast_revision"].fillna(0))
)


# --------------------------------------------------
# 4. Remove rows without historical information
# --------------------------------------------------

df = df.dropna(
    subset=["historical_error"]
).reset_index(drop=True)


# --------------------------------------------------
# 5. Save
# --------------------------------------------------

df.to_csv(
    "data/processed/features.csv",
    index=False
)


# --------------------------------------------------
# 6. Display results
# --------------------------------------------------

print("===== FEATURE ENGINEERING =====")

print("Rows:", len(df))

print("\nNew features:")
print([
    "historical_error",
    "forecast_revision",
    "forecast_stability"
])

print("\nSample:")

print(
    df[
        [
            "region",
            "lead_day",
            "rainfall_error",
            "historical_error",
            "forecast_revision",
            "forecast_stability",
            "bust"
        ]
    ].head(15)
)

print("\nSaved to:")
print("data/processed/features.csv")