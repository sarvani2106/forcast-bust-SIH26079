from backend.real_data import (
    get_real_data,
    get_latest_by_lead_day
)

df = get_real_data()

print("=" * 70)
print("REAL DATA BACKEND TEST")
print("=" * 70)

print(f"Rows       : {len(df):,}")
print(f"Columns    : {len(df.columns)}")
print(f"Date range : {df['forecast_date'].min()} → {df['forecast_date'].max()}")

for day in [1, 5, 10]:

    data = get_latest_by_lead_day(day)

    print(
        f"\nLead Day {day}: "
        f"{len(data):,} grid points"
    )

    if not data.empty:
        row = data.iloc[0]

        print(
            f"Example: "
            f"lat={row['LATITUDE']}, "
            f"lon={row['LONGITUDE']}, "
            f"rain={row['forecast_rainfall']:.2f} mm"
        )

print("\nDONE")