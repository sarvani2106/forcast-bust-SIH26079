import xarray as xr

file = "data/raw/ncmrwf_2025-09-01.grib"

ds = xr.open_dataset(file, engine="cfgrib")

tp = ds["tp"]

print("Units:", tp.attrs.get("units"))
print("Min:", float(tp.min()))
print("Max:", float(tp.max()))

print("\nMean by lead day:")
print(tp.mean(dim=["latitude", "longitude"]).values)