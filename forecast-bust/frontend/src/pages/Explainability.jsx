import { useState } from "react";
import { getRealExplainability } from "../api/explainabilityApi";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import RiskBadge from "../components/common/RiskBadge";
import Header from "../components/layout/Header";
import { NavLink } from "react-router-dom";

const featureLabels = {
  lead_day: "Lead Day",
  lead_day_squared: "Lead Day Squared",
  LATITUDE: "Latitude",
  LONGITUDE: "Longitude",
  latitude_abs: "Absolute Latitude",
  longitude_abs: "Absolute Longitude",
  forecast_rainfall: "Rainfall Forecast",
  forecast_rainfall_squared: "Rainfall Forecast Squared",
  log_forecast_rainfall: "Log Rainfall Forecast",
  previous_forecast: "Previous Forecast",
  forecast_revision: "Forecast Revision",
  forecast_stability: "Forecast Stability",
  historical_mae: "Historical MAE",
};

function formatProbability(value) {
  if (value === undefined || value === null) return "No data";
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatFeatureName(feature) {
  return featureLabels[feature] ?? feature.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatImpact(value) {
  if (typeof value !== "number") return "No data";
  return `${value > 0 ? "+" : ""}${value.toFixed(5)}`;
}

function Explainability() {
  const [coordinates, setCoordinates] = useState({ latitude: "", longitude: "" });
  const [leadDay, setLeadDay] = useState(5);
  const [explanation, setExplanation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [hasRequested, setHasRequested] = useState(false);

  const loadExplanation = async (event) => {
    event?.preventDefault();
    if (!Number.isFinite(Number(coordinates.latitude)) || coordinates.latitude === "" ||
        !Number.isFinite(Number(coordinates.longitude)) || coordinates.longitude === "") return;

    setHasRequested(true);
    setIsLoading(true);
    setHasError(false);
    try {
      const result = await getRealExplainability(
        Number(coordinates.latitude),
        Number(coordinates.longitude),
        leadDay,
      );
      setExplanation(result);
    } catch {
      setHasError(true);
      setExplanation(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="explainability-page">
      <Header title="Model Explainability" description="SHAP contributions from the calibrated real-data model" context="Real September 2025 forecast grid · calibrated model" />

      <form className="explainability-monitoring" aria-label="Real forecast point selection" onSubmit={loadExplanation}>
        <div className="explainability-monitoring-copy">
          <span className="dashboard-kicker">Forecast monitoring</span>
          <p>Enter an exact real forecast grid coordinate and lead day to inspect calibrated model contributions.</p>
        </div>

        <div className="explainability-selectors">
          <label className="explainability-select">
            <span>Latitude</span>
            <input type="number" step="any" required value={coordinates.latitude} onChange={(event) => setCoordinates((current) => ({ ...current, latitude: event.target.value }))} />
          </label>
          <label className="explainability-select">
            <span>Longitude</span>
            <input type="number" step="any" required value={coordinates.longitude} onChange={(event) => setCoordinates((current) => ({ ...current, longitude: event.target.value }))} />
          </label>
          <label className="explainability-select">
            <span>Lead Day</span>
            <select value={leadDay} onChange={(event) => setLeadDay(Number(event.target.value))}>
              {Array.from({ length: 10 }, (_, index) => index + 1).map((day) => (
                <option key={day} value={day}>Day {day}</option>
              ))}
            </select>
          </label>
          <button className="primary-button" type="submit" disabled={isLoading}>
            {isLoading ? "Generating…" : "Generate explanation"}
          </button>
        </div>
      </form>

      {isLoading && <LoadingState />}
      {!isLoading && hasError && <ErrorState message="Unable to load real-data SHAP explanation. Check that the coordinates match a real grid point and retry." />}
      {!isLoading && !hasRequested && <EmptyState message="Enter a real grid coordinate to load its model prediction and SHAP factors." />}
      {!isLoading && hasRequested && !hasError && !explanation && <EmptyState message="No real explanation data available for this selection." />}

      {!isLoading && explanation && (
        <>
          <section className="explainability-decision card" aria-labelledby="model-decision-title">
            <div className="explainability-section-header">
              <div>
                <span className="dashboard-kicker">Prediction context</span>
                <h2 id="model-decision-title">Model Decision</h2>
              </div>
            </div>
            <div className="explainability-decision-grid">
              <div><span>Forecast Date</span><strong>{explanation.forecast_date ?? "No data"}</strong></div>
              <div><span>Latitude / Longitude</span><strong>{explanation.latitude}, {explanation.longitude}</strong></div>
              <div><span>Lead Day</span><strong>Day {explanation.lead_day}</strong></div>
              <div><span>Risk</span><RiskBadge risk={explanation.risk} /></div>
              <div><span>Bust Probability</span><strong>{formatProbability(explanation.bust_probability)}</strong></div>
              <div><span>Confidence</span><strong>{formatProbability(explanation.confidence)}</strong></div>
              <div><span>Prediction</span><strong>{explanation.bust_prediction ?? "No data"}</strong></div>
            </div>
          </section>

          {explanation.factors?.length ? (
            <section className="explainability-factors card" aria-labelledby="factors-title">
              <div className="explainability-section-header">
                <div>
                  <span className="dashboard-kicker">Model contribution</span>
                  <h2 id="factors-title">Top 5 SHAP Factors</h2>
                  <p>Exact SHAP contributions for the calibrated model’s predicted bust probability.</p>
                </div>
              </div>
              <div className="explainability-factor-list">
                {explanation.factors.map((factor) => (
                  <article className={`explainability-factor-row ${factor.direction === "increases" ? "is-positive" : factor.direction === "reduces" ? "is-negative" : "is-neutral"}`} key={factor.feature}>
                    <div className="explainability-factor-heading">
                      <strong>{formatFeatureName(factor.feature)}</strong>
                      <span>Value {factor.feature_value ?? "No data"} · Impact <b>{formatImpact(factor.impact)}</b> · {factor.direction ?? "No data"}</span>
                    </div>
                    <p>{factor.explanation ?? "No data"}</p>
                  </article>
                ))}
              </div>
            </section>
          ) : <EmptyState message="No SHAP factors available for this real forecast point." />}

          <aside className="explainability-note" aria-labelledby="interpretation-title">
            <span className="dashboard-kicker" id="interpretation-title">Model interpretation</span>
            <p>SHAP values describe each feature’s contribution to the model output. They are model-derived reliability factors, not physical causes.</p>
          </aside>

          <NavLink className="explainability-analysis-link" to="/forecast">
            View Forecast Analysis <span aria-hidden="true">→</span>
          </NavLink>
        </>
      )}
    </div>
  );
}

export default Explainability;
