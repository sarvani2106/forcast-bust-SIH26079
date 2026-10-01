import pandas as pd

# Load dataset
df = pd.read_csv("data/raw/weather_forecasts.csv")

# Calculate absolute forecast error
df["rainfall_error"] = (
    df["rainfall_forecast"] - df["rainfall_actual"]
).abs()

# For our first prototype:
# A forecast is considered a "bust" if the error is >= 30 mm
BUST_THRESHOLD = 30

df["bust"] = (
    df["rainfall_error"] >= BUST_THRESHOLD
).astype(int)

# Create readable label
df["bust_label"] = df["bust"].map({
    0: "Normal",
    1: "Bust"
})

# Save processed dataset
df.to_csv("data/processed/forecast_errors.csv", index=False)
print("===== FORECAST VERIFICATION =====")
print("Total rows:", len(df))

print("\nError statistics:")
print(df["rainfall_error"].describe())

print("\nBust distribution:")
print(df["bust_label"].value_counts())

print("\nSample:")
print(
    df[
        [
            "region",
            "lead_day",
            "rainfall_forecast",
            "rainfall_actual",
            "rainfall_error",
            "bust_label"
        ]
    ].head(15)
)