# ForeSight AI

### AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts

ForeSight AI is an AI-powered forecast reliability system developed for
Smart India Hackathon 2026 – Problem Statement SIH26079.

The system identifies potential forecast busts in medium-range weather
forecasts and provides forecast probability, confidence, risk levels,
and explainable insights.

## 🚀 Key Features

- Day 1–Day 10 forecast reliability analysis
- Grid-level forecast bust risk detection
- Forecast bust probability and confidence
- High / Moderate / Low risk classification
- SHAP-based explainability
- Historical forecast performance analysis
- Interactive India risk map
- REST APIs using FastAPI
- Interactive dashboard using React + Vite

## 🧠 AI/ML

The system uses a Random Forest model to predict forecast-bust
probability using forecast, temporal, spatial and historical-error
features.

SHAP is used to explain the factors influencing individual predictions.

## 📊 Data

The prototype uses:

- NCMRWF medium-range forecast data
- IMD observed rainfall data

The data is processed and aligned based on forecast date, lead day
and spatial grid.

## 🏗️ System Architecture

NCMRWF Forecast Data + IMD Observations
        ↓
Data Processing
        ↓
Feature Engineering
        ↓
AI/ML Model
        ↓
Forecast Bust Probability
        ↓
SHAP Explainability
        ↓
FastAPI Backend
        ↓
React + Vite Dashboard

## 🛠️ Technology Stack

### Frontend
- React
- Vite
- Leaflet
- Chart.js

### Backend
- Python
- FastAPI

### AI/ML
- Scikit-learn
- Random Forest
- SHAP

### Database
- PostgreSQL

## 📈 Prototype Results

- 1.44M+ forecast records processed
- 4,962 grid points analysed
- Day 1–Day 10 forecast horizon
- 67.5% bust recall on the real-data test set
- 84.7% ROC-AUC on the real-data test set

## 💻 Running the Project

### Backend

```bash
uvicorn backend.main:app --reload
