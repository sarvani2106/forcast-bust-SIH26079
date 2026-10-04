import xarray as xr

file = "data/raw/ncmrwf_2025-09-01.grib"

ds = xr.open_dataset(file, engine="cfgrib")

print(ds)
print("\nVariables:")
print(list(ds.data_vars))

print("\nCoordinates:")
print(ds.coords)

print("\nAttributes:")
print(ds.attrs)