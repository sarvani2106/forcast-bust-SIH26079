import { useEffect, useState } from "react";
import { getRegions } from "../api/forecastApi";
import { getExplainability } from "../api/explainabilityApi";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import RiskBadge from "../components/common/RiskBadge";
import Header from "../components/layout/Header";
import { NavLink } from "react-router-dom";

const featureLabels = {
  historical_mae: "Historical MAE",
  weather_variability: "Weather Variability",
  lead_day: "Lead Day",
  rainfall_forecast: "Rainfall Forecast",
  forecast_revision: "Forecast Revision",
  forecast_stability: "Forecast Stability",
  previous_forecast: "Previous Forecast",
};

function formatProbability(value) {
  if (value === undefined || value === null) return null;

  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatFeatureName(feature) {
  if (featureLabels[feature]) return featureLabels[feature];

  if (feature.startsWith("weather_regime_")) {
    const regime = feature.slice("weather_regime_".length).replaceAll("_", " ");
    return `Weather Regime: ${regime}`;
  }

  return feature
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatImpact(value) {
  if (typeof value !== "number") return value;

  return `${value > 0 ? "+" : ""}${value.toFixed(4)}`;
}

function Explainability() {
  const [regions, setRegions] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState("");
  const [leadDay, setLeadDay] = useState(5);
  const [explanation, setExplanation] = useState(null);
  const [isRegionsLoading, setIsRegionsLoading] = useState(true);
  const [isExplanationLoading, setIsExplanationLoading] = useState(false);
  const [hasRegionsError, setHasRegionsError] = useState(false);
  const [hasExplanationError, setHasExplanationError] = useState(false);

  useEffect(() => {
    let isCurrentRequest = true;

    getRegions()
      .then((data) => {
        if (!isCurrentRequest) return;

        const availableRegions = data.regions;
        setRegions(availableRegions);
        setSelectedRegion(availableRegions[0] ?? "");
      })
      .catch(() => {
        if (isCurrentRequest) {
          setHasRegionsError(true);
        }
      })
      .finally(() => {
        if (isCurrentRequest) {
          setIsRegionsLoading(false);
        }
      });

    return () => {
      isCurrentRequest = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedRegion) {
      setExplanation(null);
      setIsExplanationLoading(false);
      return undefined;
    }

    let isCurrentRequest = true;

    setIsExplanationLoading(true);
    setHasExplanationError(false);

    getExplainability(selectedRegion, leadDay)
      .then((data) => {
        if (isCurrentRequest) {
          setExplanation(data);
        }
      })
      .catch(() => {
        if (isCurrentRequest) {
          setHasExplanationError(true);
        }
      })
      .finally(() => {
        if (isCurrentRequest) {
          setIsExplanationLoading(false);
        }
      });

    return () => {
      isCurrentRequest = false;
    };
  }, [leadDay, selectedRegion]);

  const isLoading = isRegionsLoading || isExplanationLoading;

  return (
    <div className="explainability-page">
      <Header title="Explainability" />

      <section className="explainability-monitoring" aria-label="Forecast monitoring">
        <div className="explainability-monitoring-copy">
          <span className="dashboard-kicker">Forecast monitoring</span>
          <p>Select a region and forecast lead day to inspect model contributions.</p>
        </div>

        <div className="explainability-selectors">
          <label className="explainability-select">
            <span>Region</span>
            <select
              value={selectedRegion}
              onChange={(event) => setSelectedRegion(event.target.value)}
              disabled={isRegionsLoading || regions.length === 0}
            >
              <option value="" disabled>
                Select a region
              </option>
              {regions.map((region) => (
                <option key={region} value={region}>
                  {region}
                </option>
              ))}
            </select>
          </label>

          <label className="explainability-select">
            <span>Lead Day</span>
            <select
              value={leadDay}
              onChange={(event) => setLeadDay(Number(event.target.value))}
              disabled={!selectedRegion}
            >
              {Array.from({ length: 10 }, (_, index) => index + 1).map((day) => (
                <option key={day} value={day}>
                  Day {day}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      {isLoading && <LoadingState />}

      {!isLoading && hasRegionsError && (
        <ErrorState message="Unable to load regions." />
      )}

      {!isLoading && !hasRegionsError && regions.length === 0 && (
        <EmptyState message="No region selected." />
      )}

      {!isLoading && !hasRegionsError && selectedRegion && hasExplanationError && (
        <ErrorState message="Unable to load explainability data." />
      )}

      {!isLoading &&
        !hasRegionsError &&
        selectedRegion &&
        !hasExplanationError &&
        explanation && (
          <>
            <section className="explainability-decision card" aria-labelledby="model-decision-title">
              <div className="explainability-section-header">
                <div>
                  <span className="dashboard-kicker">Prediction context</span>
                  <h2 id="model-decision-title">Model Decision</h2>
                </div>
              </div>
              <div className="explainability-decision-grid">
                {explanation.region !== undefined && (
                  <div>
                    <span>Region</span>
                    <strong>{explanation.region}</strong>
                  </div>
                )}
                {explanation.lead_day !== undefined && (
                  <div>
                    <span>Lead Day</span>
                    <strong>Day {explanation.lead_day}</strong>
                  </div>
                )}
                {explanation.risk !== undefined && (
                  <div>
                    <span>Risk</span>
                    <RiskBadge risk={explanation.risk} />
                  </div>
                )}
                {explanation.bust_probability !== undefined && (
                  <div>
                    <span>Bust Probability</span>
                    <strong>{formatProbability(explanation.bust_probability)}</strong>
                  </div>
                )}
                {explanation.confidence !== undefined && (
                  <div>
                    <span>Confidence</span>
                    <strong>{formatProbability(explanation.confidence)}</strong>
                  </div>
                )}
              </div>
            </section>

            {explanation.top_factors?.length ? (
              <section className="explainability-factors card" aria-labelledby="factors-title">
                <div className="explainability-section-header">
                  <div>
                    <span className="dashboard-kicker">Model contribution</span>
                    <h2 id="factors-title">Top Contributing Factors</h2>
                    <p>Features with the strongest influence on this prediction.</p>
                  </div>
                </div>
                <div className="explainability-factor-list">
                  {explanation.top_factors.map((factor, index) => (
                    <article
                      className={`explainability-factor-row ${
                        factor.impact > 0 ? "is-positive" : "is-negative"
                      }`}
                      key={`${factor.feature}-${index}`}
                    >
                      <div className="explainability-factor-heading">
                        <strong>{formatFeatureName(factor.feature)}</strong>
                        <span>
                          Impact <b>{formatImpact(factor.impact)}</b>
                        </span>
                      </div>
                      <p>{factor.explanation}</p>
                    </article>
                  ))}
                </div>
              </section>
            ) : (
              <EmptyState message="No explanation factors available." />
            )}

            <aside className="explainability-note" aria-labelledby="interpretation-title">
              <span className="dashboard-kicker" id="interpretation-title">
                Model interpretation
              </span>
              <p>
                These factors show how the model inputs influenced the selected
                prediction. They represent model contributions and should not be
                interpreted as independent causes.
              </p>
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