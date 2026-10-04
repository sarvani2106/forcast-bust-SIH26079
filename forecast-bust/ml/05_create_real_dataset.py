import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw")
IMD_FILE = RAW_DIR / "imd_rainfall_2025.nc"
OUTPUT = "data/processed/real_forecast_dataset_aug_sep.csv"

# --------------------------------------------------
# 1. Load IMD observations
# --------------------------------------------------

imd = xr.open_dataset(IMD_FILE)
obs = imd["RAINFALL"]

print("IMD loaded:", obs.shape)

# --------------------------------------------------
# 2. Find all August + September GRIB files
# --------------------------------------------------

grib_files = sorted(
    list(RAW_DIR.glob("ncmrwf_2025-08-*.grib")) +
    list(RAW_DIR.glob("ncmrwf_2025-09-*.grib"))
)

print(f"\nFound {len(grib_files)} GRIB files.")

if not grib_files:
    raise FileNotFoundError("No NCMRWF GRIB files found.")

all_forecasts = []

# --------------------------------------------------
# 3. Process each forecast initialization
# --------------------------------------------------

for file in grib_files:

    date_str = file.stem.replace("ncmrwf_", "")

    print(f"\nProcessing {date_str}...")

    try:
        ncm = xr.open_dataset(
            file,
            engine="cfgrib"
        )

        tp = ncm["tp"]

        # --------------------------------------------------
        # Convert accumulated precipitation → daily rainfall
        # --------------------------------------------------

        daily_tp = tp.diff("step", label="upper")

        first_day = tp.isel(step=0)

        daily_tp = xr.concat(
            [first_day, daily_tp],
            dim="step"
        )

        # Remove tiny numerical negative values
        daily_tp = daily_tp.clip(min=0)

        # --------------------------------------------------
        # Interpolate NCMRWF onto IMD grid
        # --------------------------------------------------

        forecast_interp = daily_tp.interp(
            latitude=obs.LATITUDE,
            longitude=obs.LONGITUDE,
            method="linear"
        )

        # --------------------------------------------------
        # Convert to DataFrame
        # --------------------------------------------------

        forecast_df = forecast_interp.to_dataframe(
            name="forecast_rainfall"
        ).reset_index()

        forecast_df["lead_day"] = (
            forecast_df["step"]
            .dt.total_seconds() / 86400
        ).astype(int)

        forecast_df["forecast_date"] = pd.Timestamp(date_str)

        forecast_df["date"] = (
            forecast_df["valid_time"]
            .dt.normalize()
        )

        forecast_df = forecast_df[
            [
                "forecast_date",
                "date",
                "lead_day",
                "latitude",
                "longitude",
                "forecast_rainfall"
            ]
        ]

        forecast_df = forecast_df.rename(
            columns={
                "latitude": "LATITUDE",
                "longitude": "LONGITUDE"
            }
        )

        # --------------------------------------------------
        # Match IMD observations
        # --------------------------------------------------

        dates_needed = forecast_df["date"].unique()

        obs_subset = obs.sel(
            TIME=dates_needed
        )

        obs_df = obs_subset.to_dataframe(
            name="actual_rainfall"
        ).reset_index()

        obs_df["date"] = (
            obs_df["TIME"]
            .dt.normalize()
        )

        obs_df = obs_df.drop(columns=["TIME"])

        # --------------------------------------------------
        # Merge
        # --------------------------------------------------

        merged = forecast_df.merge(
            obs_df,
            on=[
                "date",
                "LATITUDE",
                "LONGITUDE"
            ],
            how="inner"
        )

        # Remove missing observations
        merged = merged.dropna(
            subset=[
                "forecast_rainfall",
                "actual_rainfall"
            ]
        )

        all_forecasts.append(merged)

        print(
            f"  Matched valid rows: {len(merged)}"
        )

        ncm.close()

    except Exception as e:

        print(
            f"  ERROR processing {date_str}: {e}"
        )

# --------------------------------------------------
# 4. Combine all forecasts
# --------------------------------------------------

if not all_forecasts:
    raise RuntimeError(
        "No forecast data was successfully processed."
    )

df = pd.concat(
    all_forecasts,
    ignore_index=True
)

# --------------------------------------------------
# 5. Calculate forecast error
# --------------------------------------------------

df["rainfall_error"] = (
    df["forecast_rainfall"]
    - df["actual_rainfall"]
).abs()

# --------------------------------------------------
# 6. Provisional bust threshold
# --------------------------------------------------

BUST_THRESHOLD_MM = 30

df["bust"] = (
    df["rainfall_error"] >= BUST_THRESHOLD_MM
).astype(int)

# --------------------------------------------------
# 7. Final columns
# --------------------------------------------------

df = df[
    [
        "forecast_date",
        "date",
        "lead_day",
        "LATITUDE",
        "LONGITUDE",
        "forecast_rainfall",
        "actual_rainfall",
        "rainfall_error",
        "bust"
    ]
]

# --------------------------------------------------
# 8. Save
# --------------------------------------------------

df.to_csv(
    OUTPUT,
    index=False
)

# --------------------------------------------------
# 9. Summary
# --------------------------------------------------

print("\n========================================")
print("REAL AUG-SEP DATASET CREATED")
print("========================================")

print("Saved:", OUTPUT)
print("Shape:", df.shape)

print("\nForecast initialization dates:")
print(
    df["forecast_date"]
    .dt.strftime("%Y-%m-%d")
    .nunique()
)

print("\nLead days:")
print(
    df["lead_day"]
    .value_counts()
    .sort_index()
)

print("\nBust distribution:")
print(
    df["bust"]
    .value_counts()
)

print("\nBust rate:")
print(
    f"{df['bust'].mean() * 100:.2f}%"
)

print("\nError statistics:")
print(
    df["rainfall_error"].describe()
)

print("\nDataset saved successfully.")