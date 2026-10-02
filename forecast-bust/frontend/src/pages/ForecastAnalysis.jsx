import { useEffect, useState } from "react";
import { getForecast, getPrediction, getRegions } from "../api/forecastApi";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import RiskBadge from "../components/common/RiskBadge";
import Header from "../components/layout/Header";

const metricLabels = [
  ["rainfall_forecast", "Forecast Rainfall"],
  ["confidence", "Confidence"],
  ["bust_probability", "Bust Probability"],
  ["risk", "Risk"],
  ["stability_index", "Stability Index"],
  ["previous_forecast", "Previous Forecast"],
  ["forecast_revision", "Forecast Revision"],
  ["historical_mae", "Historical MAE"],
];

function formatProbability(value) {
  if (value === undefined || value === null) return null;

  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatMetricValue(field, value) {
  if (field === "confidence" || field === "bust_probability") {
    return formatProbability(value);
  }

  if (typeof value !== "number") return value;

  return value.toLocaleString("en-US", {
    maximumFractionDigits: field === "stability_index" ? 4 : 2,
  });
}

function PredictionMetric({ field, label, prediction }) {
  if (prediction[field] === undefined || prediction[field] === null) {
    return null;
  }

  return (
    <div className={`forecast-prediction-metric metric-${field}`}>
      <span className="forecast-prediction-label">{label}</span>
      {field === "risk" ? (
        <RiskBadge risk={prediction[field]} />
      ) : (
        <strong>{formatMetricValue(field, prediction[field])}</strong>
      )}
    </div>
  );
}

function ForecastAnalysis() {
  const [regions, setRegions] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState("");
  const [leadDay, setLeadDay] = useState(5);
  const [prediction, setPrediction] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [isRegionsLoading, setIsRegionsLoading] = useState(true);
  const [isDataLoading, setIsDataLoading] = useState(false);
  const [hasRegionsError, setHasRegionsError] = useState(false);
  const [hasDataError, setHasDataError] = useState(false);

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
      setPrediction(null);
      setForecast(null);
      setIsDataLoading(false);
      return undefined;
    }

    let isCurrentRequest = true;

    setIsDataLoading(true);
    setHasDataError(false);

    Promise.all([
      getPrediction(selectedRegion, leadDay),
      getForecast(selectedRegion),
    ])
      .then(([predictionData, forecastData]) => {
        if (!isCurrentRequest) return;

        setPrediction(predictionData);
        setForecast(forecastData);
      })
      .catch(() => {
        if (isCurrentRequest) {
          setHasDataError(true);
        }
      })
      .finally(() => {
        if (isCurrentRequest) {
          setIsDataLoading(false);
        }
      });

    return () => {
      isCurrentRequest = false;
    };
  }, [leadDay, selectedRegion]);

  const isLoading = isRegionsLoading || isDataLoading;

  return (
    <div className="forecast-analysis-page">
      <Header title="Forecast Analysis" />

      <section
        className="forecast-analysis-controls"
        aria-label="Forecast analysis controls"
      >
        <div className="forecast-analysis-intro">
          <span className="dashboard-kicker">Forecast monitoring</span>
          <p>Inspect forecast reliability and bust risk for a selected region.</p>
        </div>

        <div className="forecast-analysis-selectors">
          <label className="forecast-analysis-select">
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

          <label className="forecast-analysis-select">
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

      {!isLoading && !hasRegionsError && selectedRegion && hasDataError && (
        <ErrorState message="Unable to load forecast data." />
      )}

      {!isLoading && !hasRegionsError && selectedRegion && !hasDataError && (
        <>
          {prediction && (
            <section
              className="forecast-prediction-section"
              aria-labelledby="prediction-title"
            >
              <div className="card forecast-prediction-card">
                <div className="card-header forecast-card-header">
                  <div>
                    <span className="dashboard-kicker">Current prediction</span>
                    <h2 id="prediction-title">{prediction.region}</h2>
                    <span className="forecast-card-context">
                      Lead Day {prediction.lead_day}
                    </span>
                  </div>
                </div>
                <div className="forecast-prediction-grid card-body">
                  {metricLabels.map(([field, label]) => (
                    <PredictionMetric
                      key={field}
                      field={field}
                      label={label}
                      prediction={prediction}
                    />
                  ))}
                </div>
              </div>
            </section>
          )}

          {forecast?.forecast_days?.length ? (
            <section
              className="forecast-reliability-section"
              aria-labelledby="forecast-table-title"
            >
              <div className="card forecast-reliability-card">
                <div className="card-header forecast-card-header">
                  <div>
                    <span className="dashboard-kicker">Forecast horizon</span>
                    <h2 id="forecast-table-title">10-Day Reliability</h2>
                  </div>
                </div>
                <div className="forecast-table-wrap">
                  <table className="forecast-reliability-table">
                    <thead>
                      <tr>
                        <th>Lead Day</th>
                        <th className="is-numeric">Forecast Rainfall</th>
                        <th className="is-numeric">Confidence</th>
                        <th className="is-numeric">Bust Probability</th>
                        <th>Risk</th>
                        <th className="is-numeric">Stability Index</th>
                      </tr>
                    </thead>
                    <tbody>
                      {forecast.forecast_days.map((item) => (
                        <tr key={item.lead_day}>
                          <td>Day {item.lead_day}</td>
                          <td className="is-numeric">
                            {formatMetricValue("rainfall_forecast", item.rainfall_forecast)}
                          </td>
                          <td className="is-numeric">
                            {formatProbability(item.confidence)}
                          </td>
                          <td className="is-numeric forecast-probability-cell">
                            {formatProbability(item.bust_probability)}
                          </td>
                          <td>
                            <RiskBadge risk={item.risk} />
                          </td>
                          <td className="is-numeric">
                            {formatMetricValue("stability_index", item.stability_index)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>
          ) : (
            <EmptyState message="No forecast data available." />
          )}
        </>
      )}
    </div>
  );
}

export default ForecastAnalysis;
