import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

create_table_sql = """
CREATE TABLE IF NOT EXISTS forecast_data (
    id SERIAL PRIMARY KEY,
    region VARCHAR(100),
    forecast_date DATE,
    lead_day INTEGER,
    weather_regime VARCHAR(50),
    weather_variability FLOAT,
    historical_mae FLOAT,
    rainfall_forecast FLOAT,
    previous_forecast FLOAT,
    forecast_revision FLOAT,
    forecast_stability FLOAT,
    rainfall_actual FLOAT,
    rainfall_error FLOAT,
    bust INTEGER
);
"""

with engine.connect() as connection:
    connection.execute(text(create_table_sql))
    connection.commit()

print("forecast_data table created successfully!")