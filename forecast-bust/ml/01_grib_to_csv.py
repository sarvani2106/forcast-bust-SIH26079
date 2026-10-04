import xarray as xr
import pandas as pd

INPUT = "data/raw/ncmrwf_2025-09-01.grib"
OUTPUT = "data/processed/ncmrwf_forecast_2025-09-01.csv"

ds = xr.open_dataset(INPUT, engine="cfgrib")

df = ds["tp"].to_dataframe().reset_index()

df = df.rename(columns={
    "step": "lead_time",
    "tp": "forecast_rainfall"
})

df["lead_day"] = (
    df["lead_time"].dt.total_seconds() / 86400
).astype(int)

df = df[
    ["valid_time", "lead_day", "latitude", "longitude", "forecast_rainfall"]
]

df.to_csv(OUTPUT, index=False)

print("Saved:", OUTPUT)
print("Shape:", df.shape)
print(df.head())
print("\nLead days:")
print(df["lead_day"].value_counts().sort_index())