import { useEffect, useState } from "react";
import { getRegions } from "../api/forecastApi";
import { getTrend } from "../api/trendApi";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import RiskBadge from "../components/common/RiskBadge";
import Header from "../components/layout/Header";

function formatProbability(value) {
  if (value === undefined || value === null) return null;

  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatNumber(value, field) {
  if (typeof value !== "number") return value;

  return value.toLocaleString("en-US", {
    maximumFractionDigits: field === "stability_index" ? 4 : 2,
  });
}

function formatDate(value) {
  if (typeof value !== "string") return value;

  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) return value;

  return new Date(year, month - 1, day).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function HistoricalPerformance() {
  const [regions, setRegions] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState("");
  const [leadDay, setLeadDay] = useState(5);
  const [trend, setTrend] = useState(null);
  const [isRegionsLoading, setIsRegionsLoading] = useState(true);
  const [isTrendLoading, setIsTrendLoading] = useState(false);
  const [hasRegionsError, setHasRegionsError] = useState(false);
  const [hasTrendError, setHasTrendError] = useState(false);

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
      setTrend(null);
      setIsTrendLoading(false);
      return undefined;
    }

    let isCurrentRequest = true;

    setIsTrendLoading(true);
    setHasTrendError(false);

    getTrend(selectedRegion, leadDay)
      .then((data) => {
        if (isCurrentRequest) {
          setTrend(data.trend);
        }
      })
      .catch(() => {
        if (isCurrentRequest) {
          setHasTrendError(true);
        }
      })
      .finally(() => {
        if (isCurrentRequest) {
          setIsTrendLoading(false);
        }
      });

    return () => {
      isCurrentRequest = false;
    };
  }, [leadDay, selectedRegion]);

  const isLoading = isRegionsLoading || isTrendLoading;
  const records = Array.isArray(trend) ? trend : [];
  const riskCounts = records.reduce(
    (counts, record) => {
      if (record.risk === "HIGH") counts.high += 1;
      if (record.risk === "MODERATE") counts.moderate += 1;
      if (record.risk === "LOW") counts.low += 1;
      return counts;
    },
    { high: 0, moderate: 0, low: 0 },
  );
  const averageBustProbability = records.length
    ? records.reduce(
        (total, record) => total + record.bust_probability,
        0,
      ) / records.length
    : null;

  return (
    <div className="historical-performance-page">
      <Header title="Historical Performance" />

      <section className="historical-monitoring" aria-label="Forecast monitoring">
        <div className="historical-monitoring-copy">
          <span className="dashboard-kicker">Forecast monitoring</span>
          <p>
            Review historical forecast behavior for a selected region and lead day.
          </p>
        </div>

        <div className="historical-selectors">
          <label className="historical-select">
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

          <label className="historical-select">
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

      {!isLoading && !hasRegionsError && selectedRegion && hasTrendError && (
        <ErrorState message="Unable to load historical data." />
      )}

      {!isLoading &&
        !hasRegionsError &&
        selectedRegion &&
        !hasTrendError &&
        (records.length ? (
          <section className="historical-records-card card" aria-labelledby="trend-title">
            <div className="historical-records-header">
              <div>
                <span className="dashboard-kicker">Historical performance</span>
                <h2 id="trend-title">Historical Forecast Records</h2>
                <p>{selectedRegion} · Lead Day {leadDay}</p>
                <span className="historical-context-note">
                  Historical observations for the selected forecast lead day.
                </span>
              </div>
              <span className="historical-record-count">
                {records.length} historical observations
              </span>
            </div>

            <div className="historical-summary-grid" aria-label="Historical summary">
              <div>
                <span>Historical Records</span>
                <strong>{records.length}</strong>
              </div>
              <div>
                <span>Average Bust Probability</span>
                <strong>{formatProbability(averageBustProbability)}</strong>
              </div>
              <div>
                <span>High Risk Records</span>
                <strong className="is-high">{riskCounts.high}</strong>
              </div>
              <div>
                <span>Moderate Risk Records</span>
                <strong className="is-moderate">{riskCounts.moderate}</strong>
              </div>
              <div>
                <span>Low Risk Records</span>
                <strong className="is-low">{riskCounts.low}</strong>
              </div>
            </div>

            <div className="historical-table-wrap">
              <table className="historical-table">
                <thead>
                  <tr>
                    <th>Forecast Date</th>
                    <th className="is-numeric">Rainfall Forecast</th>
                    <th className="is-numeric">
                      <span title="Difference between the current and previous forecast.">
                        Forecast Revision
                      </span>
                    </th>
                    <th className="is-numeric">
                      <span title="Indicates how stable the forecast is.">
                        Stability Index
                      </span>
                    </th>
                    <th className="is-numeric">
                      <span title="Model-estimated probability of a forecast bust.">
                        Bust Probability
                      </span>
                    </th>
                    <th>Risk</th>
                  </tr>
                </thead>
                  <tbody>
                    {records.map((item, index) => (
                      <tr key={`${item.forecast_date}-${index}`}>
                        <td>{formatDate(item.forecast_date)}</td>
                        <td className="is-numeric">
                          {formatNumber(item.rainfall_forecast, "rainfall_forecast")}
                        </td>
                        <td className="is-numeric">
                          {formatNumber(item.forecast_revision, "forecast_revision")}
                        </td>
                        <td className="is-numeric">
                          {formatNumber(item.stability_index, "stability_index")}
                        </td>
                        <td className="is-numeric historical-probability">
                          {formatProbability(item.bust_probability)}
                        </td>
                        <td><RiskBadge risk={item.risk} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
          </section>
        ) : (
          <EmptyState message="No historical records available for this region and lead day." />
        ))}
    </div>
  );
}

export default HistoricalPerformance;
