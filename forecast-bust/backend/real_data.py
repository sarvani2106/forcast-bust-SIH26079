import os
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "real_ml_dataset.csv"
)

df = pd.read_csv(DATA_PATH)

df["forecast_date"] = pd.to_datetime(df["forecast_date"])

FEATURES = [
    "lead_day",
    "lead_day_squared",
    "LATITUDE",
    "LONGITUDE",
    "latitude_abs",
    "longitude_abs",
    "forecast_rainfall",
    "forecast_rainfall_squared",
    "log_forecast_rainfall",
    "previous_forecast",
    "forecast_revision",
    "forecast_stability",
    "historical_mae"
]


def get_real_data():
    return df


def get_latest_forecast(
    latitude: float,
    longitude: float,
    lead_day: int
):
    data = df[
        (df["LATITUDE"] == latitude)
        & (df["LONGITUDE"] == longitude)
        & (df["lead_day"] == lead_day)
    ].sort_values("forecast_date")

    if data.empty:
        return None

    return data.iloc[-1]


def get_latest_by_lead_day(lead_day: int):
    data = df[
        df["lead_day"] == lead_day
    ]

    if data.empty:
        return pd.DataFrame()

    latest_date = data["forecast_date"].max()

    return data[
        data["forecast_date"] == latest_date
    ].copy()