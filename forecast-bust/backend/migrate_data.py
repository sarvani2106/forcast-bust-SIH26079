import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Load CSV
df = pd.read_csv("data/processed/prototype_dataset.csv")

# Rename date column
df = df.rename(columns={
    "date": "forecast_date"
})

# Convert to PostgreSQL DATE format
df["forecast_date"] = pd.to_datetime(
    df["forecast_date"]
).dt.date

# Insert data
df.to_sql(
    "forecast_data",
    engine,
    if_exists="append",
    index=False,
    chunksize=500
)

print(f"Successfully inserted {len(df)} rows into PostgreSQL!")