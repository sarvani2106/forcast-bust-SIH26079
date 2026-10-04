from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import numpy as np
import os
import shap
from backend.real_model import model, BUST_THRESHOLD
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from backend.real_data import get_latest_by_lead_day, get_real_data
from backend.real_model import predict_real
from backend.real_model import model as real_model
from backend.real_model import FEATURES as REAL_FEATURES


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
        "weather_regime": row["weather_regime"],
        "weather_variability": round(float(row["weather_variability"]), 4),
        "forecast_revision": round(float(row["forecast_revision"]), 4),
        "forecast_stability": round(float(row["forecast_stability"]), 4),
        "historical_mae": round(float(row["historical_mae"]), 4),
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
        "weather_variability": round(
            float(row["weather_variability"]),
            2
        ),
        "forecast_stability": round(
            float(row["forecast_stability"]),
            4
        ),
        "weather_regime": row["weather_regime"],

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
            ),
            "forecast_revision": round(
                float(row["forecast_revision"]),
                2
            ),
            "forecast_stability": round(
                float(row["forecast_stability"]),
                4
            ),
            "previous_forecast": round(
                float(row["previous_forecast"]),
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


def get_shap_values(model_input):
    """Return class-1 SHAP values for one model input across SHAP versions."""
    raw_values = explainer.shap_values(model_input)

    if isinstance(raw_values, list):
        return raw_values[1][0]

    values = raw_values[0]
    if getattr(values, "ndim", 1) == 2:
        values = values[:, 1]
    return values.flatten()


def format_feature_value(feature, value):
    if feature.startswith("weather_regime_"):
        return "present" if value == 1 else "not present"
    if feature == "lead_day":
        return f"Day {int(value)}"
    if feature == "forecast_stability":
        return f"{float(value):.3f}"
    return f"{float(value):.2f}"


def build_factor_explanation(feature, actual_value, impact):
    direction = "increases" if impact > 0 else "reduces" if impact < 0 else "does not materially change"
    value_text = format_feature_value(feature, actual_value)
    if feature == "historical_mae":
        subject = "Historical forecast error"
        context = "forecast reliability"
    elif feature == "forecast_revision":
        subject = "Forecast revision"
        context = "forecast uncertainty"
    elif feature == "forecast_stability":
        subject = "Forecast stability"
        context = "forecast reliability"
    elif feature == "weather_variability":
        subject = "Weather variability"
        context = "forecast uncertainty"
    elif feature == "lead_day":
        subject = "Forecast lead time"
        context = "forecast uncertainty"
    elif feature == "previous_forecast":
        subject = "Previous forecast"
        context = "forecast reliability"
    elif feature == "rainfall_forecast":
        subject = "Predicted rainfall"
        context = "the model's bust-risk estimate"
    else:
        subject = feature.replace("weather_regime_", "Weather regime ")
        context = "the model's bust-risk estimate"

    return (
        f"{subject} is {value_text} and {direction} {context}. "
        f"Signed SHAP impact: {impact:+.4f}. This is a model-derived "
        "reliability indicator, not proof of a physical meteorological cause."
    )


def build_reliability_reasons(row, prediction):
    """Describe available forecast-time indicators without inventing causes."""
    reasons = []
    indicators = [
        (
            "historical_mae",
            "model-derived factor",
            f"Historical forecast error is {float(row['historical_mae']):.2f}; "
            "it reflects past forecast reliability for this input.",
        ),
        (
            "forecast_revision",
            "reliability indicator",
            f"Forecast revision is {float(row['forecast_revision']):.2f}; "
            "larger revisions indicate the forecast is changing more.",
        ),
        (
            "forecast_stability",
            "reliability indicator",
            f"Forecast stability is {float(row['forecast_stability']):.3f}; "
            "lower values indicate a less stable forecast.",
        ),
        (
            "weather_variability",
            "meteorological indicator",
            f"Weather variability is {float(row['weather_variability']):.2f}; "
            "it indicates changing conditions represented in the dataset.",
        ),
        (
            "lead_day",
            "reliability indicator",
            f"Lead time is Day {int(row['lead_day'])}; longer horizons generally "
            "provide less forecast certainty.",
        ),
    ]
    for feature, category, message in indicators:
        reasons.append(
            {
                "feature": feature,
                "category": category,
                "value": round(float(row[feature]), 4),
                "message": message,
            }
        )
    reasons.append(
        {
            "feature": "prediction",
            "category": "model-derived factor",
            "value": prediction["bust_probability"],
            "message": (
                f"The model estimates {prediction['bust_probability']:.1%} "
                f"bust probability for the selected input."
            ),
        }
    )
    return reasons


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

    values = get_shap_values(model_input)

    contributions = []

    for feature, impact in zip(FEATURES, values):
        actual_value = float(model_input.iloc[0][feature])
        signed_impact = float(impact)

        contributions.append({
            "feature": feature,
            "value": actual_value,
            "shap_impact": round(signed_impact, 4),
            "feature_value": actual_value,
            "impact": round(signed_impact, 4),
            "direction": (
                "increases"
                if signed_impact > 0
                else "reduces"
                if signed_impact < 0
                else "neutral"
            ),
            "explanation": build_factor_explanation(
                feature,
                actual_value,
                signed_impact,
            ),
        })

    # Sort by absolute impact
    contributions.sort(
        key=lambda x: abs(x["impact"]),
        reverse=True
    )

    prediction = predict_row(row)
    top_factors = contributions[:5]

    return {
        "region": region,
        "lead_day": lead_day,
        "bust_probability": prediction["bust_probability"],
        "confidence": prediction["confidence"],
        "risk": prediction["risk"],
        "factors": top_factors,
        "top_factors": top_factors,
        "reliability_reasons": build_reliability_reasons(row, prediction),
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
_real_shap_explainer = None


def get_real_shap_explainer():
    """Build exact SHAP explanations for the calibrated real-model probability."""
    global _real_shap_explainer

    if _real_shap_explainer is None:
        real_rows = get_real_data().sort_values(
            ["forecast_date", "lead_day", "LATITUDE", "LONGITUDE"]
        )
        reference = real_rows.loc[:, REAL_FEATURES].iloc[[0]]

        def calibrated_bust_probability(values):
            model_input = pd.DataFrame(values, columns=REAL_FEATURES)
            return real_model.predict_proba(model_input)[:, 1]

        masker = shap.maskers.Independent(reference)
        _real_shap_explainer = shap.Explainer(
            calibrated_bust_probability,
            masker,
            algorithm="exact",
        )

    return _real_shap_explainer


def explain_real_feature(feature, impact):
    """Describe a model contribution without claiming physical causation."""
    if impact > 0:
        direction = "increases"
        probability_direction = "higher"
    elif impact < 0:
        direction = "reduces"
        probability_direction = "lower"
    else:
        direction = "neutral"
        probability_direction = "unchanged"

    labels = {
        "lead_day": "Lead day",
        "lead_day_squared": "Lead day squared",
        "LATITUDE": "Latitude",
        "LONGITUDE": "Longitude",
        "latitude_abs": "Absolute latitude",
        "longitude_abs": "Absolute longitude",
        "forecast_rainfall": "Forecast rainfall",
        "forecast_rainfall_squared": "Forecast rainfall squared",
        "log_forecast_rainfall": "Log forecast rainfall",
        "previous_forecast": "Previous forecast",
        "forecast_revision": "Forecast revision",
        "forecast_stability": "Forecast stability",
        "historical_mae": "Historical MAE",
    }
    feature_name = labels.get(feature, feature.replace("_", " "))

    if impact == 0:
        explanation = f"{feature_name} did not shift the predicted bust probability for this row."
    else:
        explanation = (
            f"This {feature_name.lower()} value contributed to {probability_direction} "
            "predicted bust probability."
        )

    return direction, explanation


@app.get("/real/explain")
def real_explain(
    latitude: float,
    longitude: float,
    lead_day: int = Query(5, ge=1, le=10),
):
    data = get_real_data()
    coordinate_tolerance = 1e-4
    coordinate_match = (
        np.isclose(data["LATITUDE"].to_numpy(dtype=float), latitude, rtol=0, atol=coordinate_tolerance)
        & np.isclose(data["LONGITUDE"].to_numpy(dtype=float), longitude, rtol=0, atol=coordinate_tolerance)
        & (data["lead_day"].to_numpy(dtype=int) == lead_day)
    )
    matching_rows = data.loc[coordinate_match]

    if matching_rows.empty:
        raise HTTPException(
            status_code=404,
            detail="No real forecast grid point found for the requested coordinates.",
        )

    row = matching_rows.sort_values("forecast_date").iloc[-1]
    model_input = pd.DataFrame(
        [[row[feature] for feature in REAL_FEATURES]],
        columns=REAL_FEATURES,
    )
    prediction = predict_real(row)
    explanation = get_real_shap_explainer()(
        model_input,
        max_evals=2 ** len(REAL_FEATURES),
    )
    impacts = np.asarray(explanation.values).reshape(-1)

    factors = []
    for feature, impact in zip(REAL_FEATURES, impacts):
        signed_impact = float(impact)
        direction, description = explain_real_feature(feature, signed_impact)
        factors.append({
            "feature": feature,
            "feature_value": float(row[feature]),
            "impact": signed_impact,
            "direction": direction,
            "explanation": description,
        })

    factors.sort(key=lambda factor: abs(factor["impact"]), reverse=True)
    top_factors = factors[:5]

    return {
        "latitude": float(row["LATITUDE"]),
        "longitude": float(row["LONGITUDE"]),
        "lead_day": int(row["lead_day"]),
        "forecast_date": str(row["forecast_date"].date()),
        **prediction,
        "factors": top_factors,
    }


@app.get("/real/prediction")
def real_prediction(
    latitude: float,
    longitude: float,
    lead_day: int = Query(5, ge=1, le=10)
):
    data = get_latest_by_lead_day(lead_day)

    if data.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No real forecast data for lead day {lead_day}"
        )

    # Find nearest available grid point
    distances = (
        (data["LATITUDE"] - latitude) ** 2
        + (data["LONGITUDE"] - longitude) ** 2
    )

    index = distances.idxmin()
    row = data.loc[index]

    prediction = predict_real(row)

    return {
        "forecast_date": str(row["forecast_date"].date()),
        "latitude": float(row["LATITUDE"]),
        "longitude": float(row["LONGITUDE"]),
        "lead_day": int(row["lead_day"]),

        "rainfall_forecast": round(
            float(row["forecast_rainfall"]), 2
        ),

        "previous_forecast": round(
            float(row["previous_forecast"]), 2
        ),

        "forecast_revision": round(
            float(row["forecast_revision"]), 2
        ),

        "historical_mae": round(
            float(row["historical_mae"]), 2
        ),

        **prediction
    }
@app.get("/real/forecast")
def real_forecast(
    latitude: float,
    longitude: float
):
    forecasts = []

    for lead_day in range(1, 11):

        data = get_latest_by_lead_day(lead_day)

        if data.empty:
            continue

        # Find nearest available grid point
        distances = (
            (data["LATITUDE"] - latitude) ** 2
            + (data["LONGITUDE"] - longitude) ** 2
        )

        index = distances.idxmin()
        row = data.loc[index]

        prediction = predict_real(row)

        forecasts.append({
            "forecast_date": str(
                row["forecast_date"].date()
            ),

            "latitude": float(
                row["LATITUDE"]
            ),

            "longitude": float(
                row["LONGITUDE"]
            ),

            "lead_day": int(
                row["lead_day"]
            ),

            "rainfall_forecast": round(
                float(row["forecast_rainfall"]),
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

            "forecast_stability": round(
                float(row["forecast_stability"]),
                4
            ),

            **prediction
        })

    if not forecasts:
        raise HTTPException(
            status_code=404,
            detail="No real forecast data available"
        )

    return {
        "requested_latitude": latitude,
        "requested_longitude": longitude,
        "forecast_days": forecasts
    }
@app.get("/real/risk-map")
def real_risk_map(
    lead_day: int = Query(5, ge=1, le=10)
):
    data = get_latest_by_lead_day(lead_day)

    if data.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No real forecast data for lead day {lead_day}"
        )

    # Features expected by the calibrated real model
    model_input = data[[
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
    ]].copy()

    # Import final calibrated model
    from backend.real_model import model, BUST_THRESHOLD

    probabilities = model.predict_proba(
        model_input
    )[:, 1]

    points = []

    for (_, row), probability in zip(
        data.iterrows(),
        probabilities
    ):
        probability = float(probability)

        if probability >= 0.60:
            risk = "HIGH"
        elif probability >= BUST_THRESHOLD:
            risk = "MODERATE"
        else:
            risk = "LOW"

        bust = probability >= BUST_THRESHOLD

        confidence = (
            probability
            if bust
            else 1 - probability
        )

        points.append({
            "latitude": round(
                float(row["LATITUDE"]), 4
            ),
            "longitude": round(
                float(row["LONGITUDE"]), 4
            ),
            "rainfall_forecast": round(
                float(row["forecast_rainfall"]), 2
            ),
            "forecast_revision": round(
                float(row["forecast_revision"]), 2
            ),
            "historical_mae": round(
                float(row["historical_mae"]), 2
            ),
            "forecast_stability": round(
                float(row["forecast_stability"]), 4
            ),
            "bust_probability": round(
                probability, 4
            ),
            "confidence": round(
                confidence, 4
            ),
            "risk": risk,
            "bust_prediction": (
                "BUST" if bust else "NORMAL"
            )
        })

    return {
        "forecast_date": str(
            data["forecast_date"].iloc[0].date()
        ),
        "lead_day": lead_day,
        "total_points": len(points),
        "points": points
    }
