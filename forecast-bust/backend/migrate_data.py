import argparse
import os
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "processed" / "prototype_dataset.csv"


def load_data() -> pd.DataFrame:
    """Load and normalize the generated dataset without changing the database."""
    df = pd.read_csv(CSV_PATH)
    if "date" not in df.columns:
        raise ValueError(f"{CSV_PATH} must contain a 'date' column")

    df = df.rename(columns={"date": "forecast_date"})
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    return df


def inspect_data(df: pd.DataFrame) -> None:
    """Explain the date range and generator behavior without DB access."""
    dates = df["forecast_date"].sort_values()
    start = dates.iloc[0]
    expected_end = pd.Timestamp("2024-12-31 18:00:00")
    actual_end = dates.iloc[-1]

    print("===== DATA INSPECTION (READ-ONLY) =====")
    print(f"Source: {CSV_PATH}")
    print(f"Rows: {len(df):,}")
    print(f"Date range: {start} -> {actual_end}")
    print(f"Expected configured end: {expected_end}")
    print("\nRows by year:")
    print(dates.dt.year.value_counts().sort_index().to_string())

    if actual_end == expected_end:
        print(
            "\nRoot cause fixed: the previous generator created 5,000 timestamps "
            "every 6 hours from 2024-01-01, which reached 2027-06-03. The "
            "generator now constrains the prototype to the 2024 calendar year."
        )
    else:
        print(
            "\nCause requires further investigation: the CSV does not match the "
            "generator's expected 6-hour date cadence."
        )

    print("\nNo database connection was opened and no rows were changed.")


def reload_database(df: pd.DataFrame) -> None:
    """Replace database rows only after the caller explicitly requests --reload."""
    from sqlalchemy import create_engine, text

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set; refusing to modify the database")

    db_df = df.copy()
    db_df["forecast_date"] = db_df["forecast_date"].dt.date
    engine = create_engine(database_url)

    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE forecast_data RESTART IDENTITY"))
        db_df.to_sql(
            "forecast_data",
            connection,
            if_exists="append",
            index=False,
            chunksize=500,
        )

    print(f"Successfully replaced forecast_data with {len(db_df):,} rows.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect generated forecast data, or explicitly replace DB rows."
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="TRUNCATE and reload forecast_data after printing the inspection.",
    )
    args = parser.parse_args()

    if args.reload:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")

    df = load_data()
    inspect_data(df)

    if args.reload:
        reload_database(df)
    else:
        print("\nDry run only. Re-run with --reload only after reviewing this report.")


if __name__ == "__main__":
    main()
