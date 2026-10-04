import xarray as xr
import numpy as np

file = "data/raw/imd_rainfall_2025.nc"

ds = xr.open_dataset(file)
rain = ds["RAINFALL"]

sep = rain.sel(TIME=slice("2025-09-02", "2025-09-11"))

values = sep.values

total = values.size
valid = np.isfinite(values).sum()
missing = np.isnan(values).sum()

print("September 2-11")
print("Shape:", values.shape)
print("Total values:", total)
print("Valid values:", valid)
print("NaN values:", missing)
print("Valid percentage:", round(valid / total * 100, 2), "%")

valid_values = values[np.isfinite(values)]

print("\nValid rainfall statistics:")
print("Min:", valid_values.min())
print("Max:", valid_values.max())
print("Mean:", valid_values.mean())

# Find an actual valid point
idx = np.argwhere(np.isfinite(values))[0]
t, lat, lon = idx

print("\nExample valid point:")
print("Date:", sep.TIME.values[t])
print("Latitude:", sep.LATITUDE.values[lat])
print("Longitude:", sep.LONGITUDE.values[lon])
print("Rainfall:", values[t, lat, lon])