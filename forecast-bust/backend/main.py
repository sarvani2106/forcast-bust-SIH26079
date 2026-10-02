from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import os
import shap

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

app = FastAPI(title="Forecast Reliability Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env")

engine = create_engine(DATABASE_URL)

# Load trained ML model
MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "models",
    "forecast_bust_model.pkl"
)
model = joblib.load(MODEL_PATH)

# SHAP explainer
explainer = shap.TreeExplainer(model)


# ============================================================
# MODEL FEATURES
# ============================================================

FEATURES = [
    "lead_day",
    "rainfall_forecast",
    "previous_forecast",
    "historical_mae",
    "weather_variability",
    "forecast_revision",
    "forecast_stability",
    "weather_regime_Normal",
    "weather_regime_Heavy Rain",
    "weather_regime_Monsoon",
    "weather_regime_Cyclonic",
    "weather_regime_Heat Wave"
]

REGIMES = [
    "Normal",
    "Heavy Rain",
    "Monsoon",
    "Cyclonic",
    "Heat Wave"
]


# ============================================================
# FEATURE PREPARATION
# ============================================================

def prepare_model_input(row):

    input_data = {
        "lead_day": row["lead_day"],
        "rainfall_forecast": row["rainfall_forecast"],
        "previous_forecast": row["previous_forecast"],
        "historical_mae": row["historical_mae"],
        "weather_variability": row["weather_variability"],
        "forecast_revision": row["forecast_revision"],
        "forecast_stability": row["forecast_stability"],
    }

    # One-hot encode weather regime
    for regime in REGIMES:
        input_data[f"weather_regime_{regime}"] = (
            1 if row["weather_regime"] == regime else 0
        )

    model_input = pd.DataFrame([input_data])

    return model_input[FEATURES]


# ============================================================
# PREDICTION
# ============================================================

def predict_row(row):

    model_input = prepare_model_input(row)

    probability = float(
        model.predict_proba(model_input)[0][1]
    )

    confidence = 1 - probability

    # Prototype risk thresholds
    if probability >= 0.60:
        risk = "HIGH"

    elif probability >= 0.30:
        risk = "MODERATE"

    else:
        risk = "LOW"

    return {
        "bust_probability": round(probability, 4),
        "confidence": round(confidence, 4),
        "risk": risk,
        "stability_index": round(
            float(row["forecast_stability"]),
            4
        )
    }


# ============================================================
# DATABASE HELPER
# ============================================================

def get_region_data(region, lead_day):

    query = text("""
        SELECT *
        FROM forecast_data
        WHERE region = :region
        AND lead_day = :lead_day
        ORDER BY forecast_date DESC
        LIMIT 1
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "region": region,
                "lead_day": lead_day
            }
        )

        row = result.mappings().first()

    return row


def get_database_status():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "connected"
    except SQLAlchemyError:
        return "unavailable"


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "status": "online",
        "database": get_database_status(),
        "model": "loaded"
    }


# ============================================================
# GET REGIONS
# ============================================================

@app.get("/regions")
def get_regions():

    query = text("""
        SELECT DISTINCT region
        FROM forecast_data
        ORDER BY region
    """)

    with engine.connect() as connection:

        result = connection.execute(query)

        regions = [
            row[0]
            for row in result.fetchall()
        ]

    return {
        "regions": regions
    }


# ============================================================
# SINGLE PREDICTION
# ============================================================

@app.get("/prediction/{region}")
def get_prediction(
    region: str,
    lead_day: int = Query(5, ge=1, le=10)
):

    row = get_region_data(
        region,
        lead_day
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Region '{region}' or lead day {lead_day} not found"
        )

    prediction = predict_row(row)

    return {

        "region": region,

        "lead_day": lead_day,

        "rainfall_forecast": round(
            float(row["rainfall_forecast"]),
            2
        ),

        "previous_forecast": round(
            float(row["previous_forecast"]),
            2
        ),

        "forecast_revision": round(
            float(row["forecast_revision"]),
            2
        ),

        "historical_mae": round(
            float(row["historical_mae"]),
            2
        ),

        **prediction
    }


# ============================================================
# 10-DAY FORECAST
# ============================================================

@app.get("/forecast/{region}")
def get_forecast(region: str):

    query = text("""
        SELECT DISTINCT ON (lead_day)
            *
        FROM forecast_data
        WHERE region = :region

        ORDER BY
            lead_day,
            forecast_date DESC
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "region": region
            }
        )

        rows = result.mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Region '{region}' not found"
        )

    forecasts = []

    for row in rows:

        prediction = predict_row(row)

        forecasts.append({

            "lead_day": row["lead_day"],

            "rainfall_forecast": round(
                float(row["rainfall_forecast"]),
                2
            ),

            "bust_probability":
                prediction["bust_probability"],

            "confidence":
                prediction["confidence"],

            "risk":
                prediction["risk"],

            "stability_index":
                prediction["stability_index"]
        })

    return {

        "region": region,

        "forecast_days": forecasts
    }


# ============================================================
# RISK SUMMARY
# ============================================================

@app.get("/risk-summary")
def get_risk_summary(
    lead_day: int = Query(5, ge=1, le=10)
):

    query = text("""
        SELECT DISTINCT ON (region)

            region,
            lead_day,
            weather_regime,
            weather_variability,
            historical_mae,
            rainfall_forecast,
            previous_forecast,
            forecast_revision,
            forecast_stability

        FROM forecast_data

        WHERE lead_day = :lead_day

        ORDER BY
            region,
            forecast_date DESC
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "lead_day": lead_day
            }
        )

        rows = result.mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No regional data found for lead day {lead_day}"
        )

    results = []

    for row in rows:

        prediction = predict_row(row)

        results.append({

            "region": row["region"],

            **prediction
        })

    return {

        "lead_day": lead_day,

        "regions": results
    }

# ============================================================
# REGION RISK MAP
# ============================================================

@app.get("/risk-map")
def get_risk_map(lead_day: int = Query(5, ge=1, le=10)):

    query = text("""
        SELECT DISTINCT ON (region)
            region,
            lead_day,
            weather_regime,
            weather_variability,
            historical_mae,
            rainfall_forecast,
            previous_forecast,
            forecast_revision,
            forecast_stability
        FROM forecast_data
        WHERE lead_day = :lead_day
        ORDER BY
            region,
            forecast_date DESC
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "lead_day": lead_day
            }
        )

        rows = result.mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No regional data found for lead day {lead_day}"
        )

    regions = []

    for row in rows:

        prediction = predict_row(row)

        regions.append({

            "region": row["region"],

            "lead_day": row["lead_day"],

            "rainfall_forecast": round(
                float(row["rainfall_forecast"]),
                2
            ),

            "bust_probability":
                prediction["bust_probability"],

            "confidence":
                prediction["confidence"],

            "risk":
                prediction["risk"],

            "stability_index":
                prediction["stability_index"],

            "weather_regime":
                row["weather_regime"],

            "weather_variability": round(
                float(row["weather_variability"]),
                2
            ),

            "historical_mae": round(
                float(row["historical_mae"]),
                2
            )
        })

    return {
        "lead_day": lead_day,
        "regions": regions
    }


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@app.get("/dashboard-summary")
def get_dashboard_summary(
    lead_day: int = Query(5, ge=1, le=10)
):

    query = text("""
        SELECT DISTINCT ON (region)
            region,
            lead_day,
            weather_regime,
            weather_variability,
            historical_mae,
            rainfall_forecast,
            previous_forecast,
            forecast_revision,
            forecast_stability
        FROM forecast_data
        WHERE lead_day = :lead_day
        ORDER BY region, forecast_date DESC
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {"lead_day": lead_day}
        ).mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No regional data found for lead day {lead_day}"
        )

    predictions = [
        {
            "region": row["region"],
            **predict_row(row)
        }
        for row in rows
    ]
    highest_risk = max(
        predictions,
        key=lambda item: item["bust_probability"]
    )
    risk_counts = {
        risk: sum(item["risk"] == risk for item in predictions)
        for risk in ("HIGH", "MODERATE", "LOW")
    }

    return {
        "lead_day": lead_day,
        "total_regions": len(predictions),
        "high_risk_count": risk_counts["HIGH"],
        "moderate_risk_count": risk_counts["MODERATE"],
        "low_risk_count": risk_counts["LOW"],
        "average_bust_probability": round(
            sum(item["bust_probability"] for item in predictions)
            / len(predictions),
            4
        ),
        "highest_risk_region": highest_risk["region"],
        "highest_risk_probability": highest_risk["bust_probability"]
    }


# ============================================================
# HISTORICAL TREND
# ============================================================

@app.get("/trend/{region}")
def get_trend(
    region: str,
    lead_day: int = Query(5, ge=1, le=10)
):

    query = text("""
        SELECT
            forecast_date,
            lead_day,
            weather_regime,
            weather_variability,
            historical_mae,
            rainfall_forecast,
            previous_forecast,
            forecast_revision,
            forecast_stability
        FROM forecast_data
        WHERE region = :region
        AND lead_day = :lead_day
        ORDER BY forecast_date ASC
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {
                "region": region,
                "lead_day": lead_day
            }
        ).mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Region '{region}' or lead day {lead_day} not found"
        )

    trend = []
    for row in rows:
        prediction = predict_row(row)
        trend.append({
            "forecast_date": str(row["forecast_date"]),
            "rainfall_forecast": round(
                float(row["rainfall_forecast"]),
                2
            ),
            "forecast_revision": round(
                float(row["forecast_revision"]),
                2
            ),
            "stability_index": prediction["stability_index"],
            "bust_probability": prediction["bust_probability"],
            "risk": prediction["risk"]
        })

    return {
        "region": region,
        "lead_day": lead_day,
        "trend": trend
    }


# ============================================================
# FEATURE DESCRIPTIONS FOR SHAP
# ============================================================

FEATURE_DESCRIPTIONS = {

    "historical_mae":
        "Historical forecast error is contributing to uncertainty.",

    "lead_day":
        "Longer forecast lead time can increase prediction uncertainty.",

    "rainfall_forecast":
        "The predicted rainfall level is influencing forecast reliability.",

    "previous_forecast":
        "The previous forecast value is influencing current reliability.",

    "forecast_revision":
        "The forecast has changed from the previous update.",

    "forecast_stability":
        "Forecast stability is influencing the reliability estimate.",

    "weather_variability":
        "Higher weather variability can make the forecast less stable.",

    "weather_regime_Normal":
        "Current weather regime is classified as normal.",

    "weather_regime_Heavy Rain":
        "Heavy-rain conditions are influencing forecast reliability.",

    "weather_regime_Monsoon":
        "Monsoon conditions are influencing forecast reliability.",

    "weather_regime_Cyclonic":
        "Cyclonic conditions can increase forecast uncertainty.",

    "weather_regime_Heat Wave":
        "Heat-wave conditions are influencing forecast reliability."
}


# ============================================================
# SHAP EXPLANATION
# ============================================================

@app.get("/explain/{region}")
def explain_prediction(
    region: str,
    lead_day: int = Query(5, ge=1, le=10)
):

    row = get_region_data(
        region,
        lead_day
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Region '{region}' or lead day {lead_day} not found"
        )

    model_input = prepare_model_input(row)

    shap_values = explainer.shap_values(
        model_input
    )

    # Handle different SHAP output formats
    if isinstance(shap_values, list):

        values = shap_values[1][0]

    else:

        values = shap_values[0]

        if len(values.shape) == 2:

            values = values[:, 1]

    values = values.flatten()

    contributions = []

    for feature, value in zip(
        FEATURES,
        values
    ):

        contributions.append({

            "feature": feature,

            "impact": round(
                float(value),
                4
            ),

            "explanation":
                FEATURE_DESCRIPTIONS.get(
                    feature,
                    "This feature is influencing the prediction."
                )
        })

    # Sort by absolute impact
    contributions.sort(
        key=lambda x: abs(x["impact"]),
        reverse=True
    )

    prediction = predict_row(row)

    return {

        "region": region,

        "lead_day": lead_day,

        "bust_probability":
            prediction["bust_probability"],

        "risk":
            prediction["risk"],

        "top_factors":
            contributions[:5]
    }


# ============================================================
# FORECAST EVOLUTION
# ============================================================

@app.get("/forecast-evolution/{region}")
def get_forecast_evolution(
    region: str,
    lead_day: int = Query(5, ge=1, le=10)
):

    query = text("""
        SELECT

            forecast_date,

            rainfall_forecast,

            previous_forecast,

            forecast_revision,

            forecast_stability

        FROM forecast_data

        WHERE region = :region

        AND lead_day = :lead_day

        ORDER BY forecast_date ASC
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "region": region,
                "lead_day": lead_day
            }
        )

        rows = result.mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Region '{region}' or lead day {lead_day} not found"
        )

    evolution = []

    for row in rows:

        evolution.append({

            "forecast_date":
                str(row["forecast_date"]),

            "rainfall_forecast":
                round(
                    float(row["rainfall_forecast"]),
                    2
                ),

            "previous_forecast":
                round(
                    float(row["previous_forecast"]),
                    2
                ),

            "revision":
                round(
                    float(row["forecast_revision"]),
                    2
                ),

            "stability_index":
                round(
                    float(row["forecast_stability"]),
                    4
                )
        })

    return {

        "region": region,

        "lead_day": lead_day,

        "evolution": evolution
    }