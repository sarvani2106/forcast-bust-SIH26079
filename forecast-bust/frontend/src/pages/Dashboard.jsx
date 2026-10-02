import { useEffect, useState } from "react";
import { getDashboardSummary, getRiskMap } from "../api/dashboardApi";
import { getExplainability } from "../api/explainabilityApi";
import { getForecast, getPrediction } from "../api/forecastApi";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import RiskBadge from "../components/common/RiskBadge";
import RiskMap from "../components/dashboard/RiskMap";
import Header from "../components/layout/Header";
import { NavLink } from "react-router-dom";

function formatProbability(value) {
  if (value === undefined || value === null) return null;

  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
}

function DashboardMetric({ label, value, tone }) {
  return (
    <article className="dashboard-metric">
      <span className="dashboard-metric-label">{label}</span>
      <strong className={`dashboard-metric-value ${tone || ""}`}>
        {value}
      </strong>
    </article>
  );
}

function Dashboard() {
  const [leadDay, setLeadDay] = useState(5);
  const [summary, setSummary] = useState(null);
  const [riskMap, setRiskMap] = useState(null);
  const [selectedRegion, setSelectedRegion] = useState("");
  const [selectedPrediction, setSelectedPrediction] = useState(null);
  const [selectedForecast, setSelectedForecast] = useState(null);
  const [selectedExplainability, setSelectedExplainability] = useState(null);
  const [isSelectedRegionLoading, setIsSelectedRegionLoading] = useState(false);
  const [hasSelectedRegionError, setHasSelectedRegionError] = useState(false);
  const [hasForecastError, setHasForecastError] = useState(false);
  const [hasExplainabilityError, setHasExplainabilityError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let isCurrentRequest = true;

    setIsLoading(true);
    setHasError(false);
    setSelectedRegion("");

    Promise.all([getDashboardSummary(leadDay), getRiskMap(leadDay)])
      .then(([summaryData, riskMapData]) => {
        if (!isCurrentRequest) return;

        setSummary(summaryData);
        setRiskMap(riskMapData);
      })
      .catch(() => {
        if (isCurrentRequest) {
          setHasError(true);
        }
      })
      .finally(() => {
        if (isCurrentRequest) {
          setIsLoading(false);
        }
      });

    return () => {
      isCurrentRequest = false;
    };
  }, [leadDay]);

  useEffect(() => {
    if (!selectedRegion) {
      setSelectedPrediction(null);
      setSelectedForecast(null);
      setSelectedExplainability(null);
      setIsSelectedRegionLoading(false);
      setHasSelectedRegionError(false);
      setHasForecastError(false);
      setHasExplainabilityError(false);
      return undefined;
    }

    let isCurrentRequest = true;

    setIsSelectedRegionLoading(true);
    setHasSelectedRegionError(false);
    setHasForecastError(false);
    setHasExplainabilityError(false);

    Promise.allSettled([
      getPrediction(selectedRegion, leadDay),
      getForecast(selectedRegion),
      getExplainability(selectedRegion, leadDay),
    ])
      .then(([predictionResult, forecastResult, explainabilityResult]) => {
        if (!isCurrentRequest) return;

        if (predictionResult.status === "fulfilled") {
          setSelectedPrediction(predictionResult.value);
        } else {
          setHasSelectedRegionError(true);
        }

        if (forecastResult.status === "fulfilled") {
          setSelectedForecast(forecastResult.value);
        } else {
          setHasForecastError(true);
        }

        if (explainabilityResult.status === "fulfilled") {
          setSelectedExplainability(explainabilityResult.value);
        } else {
          setHasExplainabilityError(true);
        }
      })
      .finally(() => {
        if (isCurrentRequest) {
          setIsSelectedRegionLoading(false);
        }
      });

    return () => {
      isCurrentRequest = false;
    };
  }, [leadDay, selectedRegion]);

  const handleLeadDayChange = (event) => {
    setSelectedRegion("");
    setLeadDay(Number(event.target.value));
  };

  return (
    <div className="dashboard-page">
      <Header title="Forecast Reliability Dashboard" />

      <section className="dashboard-control-bar" aria-label="Dashboard controls">
        <div>
          <span className="dashboard-kicker">Forecast monitoring</span>
          <strong>Risk posture by forecast lead day</strong>
        </div>
        <label className="dashboard-select-label">
          <span>Forecast Lead Day</span>
          <select
            value={leadDay}
            onChange={handleLeadDayChange}
            aria-label="Forecast Lead Day"
          >
            {Array.from({ length: 10 }, (_, index) => index + 1).map((day) => (
              <option key={day} value={day}>
                Day {day}
              </option>
            ))}
          </select>
        </label>
      </section>

      {isLoading && <LoadingState />}

      {!isLoading && hasError && <ErrorState />}

      {!isLoading && !hasError && summary && (
        <>
          <section className="dashboard-summary-section" aria-labelledby="dashboard-summary-title">
            <div className="dashboard-section-heading">
              <div>
                <span className="dashboard-kicker">Current model output</span>
                <h2 id="dashboard-summary-title">Reliability Summary</h2>
              </div>
              <span className="dashboard-lead-indicator">
                Lead day {summary.lead_day}
              </span>
            </div>

            <div className="dashboard-summary-grid">
              <DashboardMetric label="Total Regions" value={summary.total_regions} />
              <DashboardMetric
                label="High Risk"
                value={summary.high_risk_count}
                tone="is-high"
              />
              <DashboardMetric
                label="Moderate Risk"
                value={summary.moderate_risk_count}
                tone="is-moderate"
              />
              <DashboardMetric
                label="Low Risk"
                value={summary.low_risk_count}
                tone="is-low"
              />
              <DashboardMetric
                label="Average Bust Probability"
                value={formatProbability(summary.average_bust_probability)}
              />
              <DashboardMetric
                label="Highest Risk Region"
                value={summary.highest_risk_region}
              />
            </div>
          </section>

          <section className="dashboard-map-section" aria-labelledby="regional-risk-title">
            <div className="dashboard-section-heading">
              <div>
                <span className="dashboard-kicker">Geographic intelligence</span>
                <h2 id="regional-risk-title">Regional Forecast Risk</h2>
                <p>Risk classification across monitored forecast regions</p>
              </div>
              <span className="dashboard-lead-indicator">
                Lead day {riskMap?.lead_day ?? summary.lead_day}
              </span>
            </div>
            <RiskMap
              key={leadDay}
              riskMap={riskMap}
              leadDay={leadDay}
              isLoading={isLoading}
              hasError={hasError}
              onSelectRegion={setSelectedRegion}
            />
          </section>

          {selectedRegion && (
            <section
              className="dashboard-selected-region"
              aria-labelledby="selected-region-title"
            >
              <div className="dashboard-selected-region-heading">
                <span className="dashboard-kicker">Selected region</span>
                <h2 id="selected-region-title">{selectedRegion}</h2>
              </div>

              {isSelectedRegionLoading && <LoadingState />}

              {!isSelectedRegionLoading && hasSelectedRegionError && (
                <ErrorState message="Unable to load selected region data." />
              )}

              {!isSelectedRegionLoading &&
                !hasSelectedRegionError &&
                selectedPrediction && (
                  <div className="dashboard-selected-region-metrics">
                    {selectedPrediction.risk !== undefined && (
                      <div>
                        <span>Risk status</span>
                        <RiskBadge risk={selectedPrediction.risk} />
                      </div>
                    )}
                    {selectedPrediction.bust_probability !== undefined && (
                      <div>
                        <span>Bust probability</span>
                        <strong>
                          {formatProbability(selectedPrediction.bust_probability)}
                        </strong>
                      </div>
                    )}
                    {selectedPrediction.confidence !== undefined && (
                      <div>
                        <span>Confidence</span>
                        <strong>
                          {formatProbability(selectedPrediction.confidence)}
                        </strong>
                      </div>
                    )}
                    {selectedPrediction.stability_index !== undefined && (
                      <div>
                        <span>Stability index</span>
                        <strong>{selectedPrediction.stability_index}</strong>
                      </div>
                    )}
                    {selectedPrediction.rainfall_forecast !== undefined && (
                      <div>
                        <span>Rainfall forecast</span>
                        <strong>{selectedPrediction.rainfall_forecast}</strong>
                      </div>
                    )}
                    {selectedPrediction.historical_mae !== undefined && (
                      <div>
                        <span>Historical MAE</span>
                        <strong>{selectedPrediction.historical_mae}</strong>
                      </div>
                    )}
                  </div>
                )}
            </section>
          )}

          {selectedRegion && !isSelectedRegionLoading && (
            <section className="dashboard-lower-grid" aria-label="Selected region analysis">
              <article className="dashboard-panel dashboard-reliability-panel">
                <div className="dashboard-panel-header">
                  <div>
                    <span className="dashboard-kicker">Forecast horizon</span>
                    <h2>Forecast Reliability</h2>
                    <p>Risk classification across the 10-day forecast horizon</p>
                  </div>
                </div>

                {hasForecastError && (
                  <ErrorState message="Unable to load forecast reliability." />
                )}

                {!hasForecastError && selectedForecast?.forecast_days?.length ? (
                  <div className="dashboard-reliability-table-wrap">
                    <table className="dashboard-reliability-table">
                      <thead>
                        <tr>
                          <th>Day</th>
                          <th>Risk</th>
                          <th>Bust Probability</th>
                          <th>Confidence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedForecast.forecast_days.map((item) => (
                          <tr key={item.lead_day}>
                            <td>Day {item.lead_day}</td>
                            <td><RiskBadge risk={item.risk} /></td>
                            <td>{formatProbability(item.bust_probability)}</td>
                            <td>{formatProbability(item.confidence)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : null}

                {!hasForecastError && !selectedForecast?.forecast_days?.length && (
                  <EmptyState message="No forecast reliability data available." />
                )}
              </article>

              <article className="dashboard-panel dashboard-explainability-panel">
                <div className="dashboard-panel-header">
                  <div>
                    <span className="dashboard-kicker">Model context</span>
                    <h2>Why is this forecast at risk?</h2>
                  </div>
                </div>

                {hasExplainabilityError && (
                  <ErrorState message="Unable to load explainability data." />
                )}

                {!hasExplainabilityError && selectedExplainability?.top_factors?.length ? (
                  <div className="dashboard-factor-preview">
                    {selectedExplainability.top_factors.slice(0, 3).map((factor, index) => (
                      <div className="dashboard-factor-row" key={`${factor.feature}-${index}`}>
                        <strong>{factor.feature}</strong>
                        <span>{factor.explanation}</span>
                      </div>
                    ))}
                    <NavLink className="dashboard-explanation-link" to="/explainability">
                      View Full Explanation <span aria-hidden="true">→</span>
                    </NavLink>
                  </div>
                ) : null}

                {!hasExplainabilityError && !selectedExplainability?.top_factors?.length && (
                  <EmptyState message="No explanation factors available." />
                )}
              </article>
            </section>
          )}
        </>
      )}
    </div>
  );
}

export default Dashboard;