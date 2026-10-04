import pandas as pd
import numpy as np

FILE = "data/processed/real_forecast_dataset_all.csv"

df = pd.read_csv(FILE)

print("Dataset shape:", df.shape)

# --------------------------------------------------
# Overall error percentiles
# --------------------------------------------------

print("\n=== OVERALL ERROR PERCENTILES ===")

percentiles = [50, 75, 80, 85, 90, 95, 97, 98, 99, 99.5]

for p in percentiles:
    value = np.percentile(df["rainfall_error"], p)
    print(f"{p:5g}th percentile: {value:.2f} mm")


# --------------------------------------------------
# Error statistics by lead day
# --------------------------------------------------

print("\n=== ERROR BY LEAD DAY ===")

lead_stats = df.groupby("lead_day")["rainfall_error"].agg(
    count="count",
    mean="mean",
    median="median",
    p90=lambda x: np.percentile(x, 90),
    p95=lambda x: np.percentile(x, 95),
    p99=lambda x: np.percentile(x, 99),
    max="max"
)

print(lead_stats.round(2).to_string())


# --------------------------------------------------
# Bust rates for different thresholds
# --------------------------------------------------

print("\n=== BUST RATE BY THRESHOLD ===")

thresholds = [10, 15, 20, 25, 30, 40, 50]

for threshold in thresholds:
    bust_rate = (
        (df["rainfall_error"] >= threshold).mean() * 100
    )

    print(
        f"{threshold:>3} mm : "
        f"{bust_rate:.2f}% "
        f"({(df['rainfall_error'] >= threshold).sum()} records)"
    )


# --------------------------------------------------
# Bust rate by lead day using 30 mm
# --------------------------------------------------

print("\n=== 30 MM BUST RATE BY LEAD DAY ===")

df["temporary_bust"] = (
    df["rainfall_error"] >= 30
)

bust_by_lead = (
    df.groupby("lead_day")["temporary_bust"]
    .mean() * 100
)

for lead, rate in bust_by_lead.items():
    print(f"Day {lead:2d}: {rate:.2f}%")


# --------------------------------------------------
# Forecast error growth
# --------------------------------------------------

print("\n=== MEAN ERROR BY LEAD DAY ===")

mean_error = df.groupby("lead_day")["rainfall_error"].mean()

for lead, error in mean_error.items():
    print(f"Day {lead:2d}: {error:.2f} mm")