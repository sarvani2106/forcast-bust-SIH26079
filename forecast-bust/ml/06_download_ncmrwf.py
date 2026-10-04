import cdsapi
from pathlib import Path
from datetime import date, timedelta

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = cdsapi.Client()

DATASET = "tigge-forecasts"

START_DATE = date(2025, 8, 1)
END_DATE = date(2025, 9, 30)

LEAD_TIMES = [
    "24", "48", "72", "96", "120",
    "144", "168", "192", "216", "240"
]

current = START_DATE

while current <= END_DATE:

    date_str = current.strftime("%Y-%m-%d")
    year = current.strftime("%Y")
    month = current.strftime("%m")
    day = current.strftime("%d")

    target = OUTPUT_DIR / f"ncmrwf_{date_str}.grib"

    # Skip files already downloaded
    if target.exists():
        print(f"Already exists: {target}")
        current += timedelta(days=1)
        continue

    request = {
        "origin": "ncmrwf",
        "year": year,
        "month": month,
        "day": day,
        "time": "00:00",
        "level_type": "single_level",
        "variable": ["total_precipitation"],
        "forecast_type": "control_forecast",
        "leadtime_hour": LEAD_TIMES,
        "data_format": "grib",
        "area": [38, 68, 6, 98]
    }

    print("\n" + "=" * 50)
    print(f"Downloading: {date_str}")
    print("=" * 50)

    try:
        client.retrieve(
            DATASET,
            request,
            str(target)
        )

        print(f"Saved: {target}")

    except Exception as e:
        print(f"FAILED: {date_str}")
        print("Error:", e)

    current += timedelta(days=1)

print("\nAll requested dates processed.")