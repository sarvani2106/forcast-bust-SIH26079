import xarray as xr

file = "data/raw/imd_rainfall_2025.nc"

ds = xr.open_dataset(file)

print(ds)
print("\nVariables:")
print(list(ds.data_vars))

print("\nCoordinates:")
print(ds.coords)

print("\nAttributes:")
print(ds.attrs)