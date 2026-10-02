import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [leadDay, setLeadDay] = useState(5);
  const [regions, setRegions] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState("Coastal Andhra");
  const [prediction, setPrediction] = useState(null);
  const [riskSummary, setRiskSummary] = useState([]);

  useEffect(() => {
    fetchRegions();
  }, []);

  useEffect(() => {
    fetchRiskSummary();
    fetchPrediction(selectedRegion);
  }, [leadDay, selectedRegion]);

  const fetchRegions = async () => {
    try {
      const response = await axios.get(`${API}/regions`);
      setRegions(response.data.regions);
    } catch (error) {
      console.error("Failed to load regions:", error);
    }
  };

  const fetchPrediction = async (region) => {
    try {
      const response = await axios.get(
        `${API}/prediction/${encodeURIComponent(region)}?lead_day=${leadDay}`
      );
      setPrediction(response.data);
    } catch (error) {
      console.error("Failed to load prediction:", error);
    }
  };

  const fetchRiskSummary = async () => {
    try {
      const response = await axios.get(
        `${API}/risk-summary?lead_day=${leadDay}`
      );
      setRiskSummary(response.data.regions);
    } catch (error) {
      console.error("Failed to load risk summary:", error);
    }
  };

  const getRiskClass = (risk) => {
    if (risk === "HIGH") return "high";
    if (risk === "MODERATE") return "moderate";
    return "low";
  };

  return (
    <div className="app">

      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-mark">F</div>
          <div>
            <h2>Forecast</h2>
            <span>Reliability Engine</span>
          </div>
        </div>

        <nav>
          <div className="nav-item active">Dashboard</div>
          <div className="nav-item">Forecast Confidence</div>
          <div className="nav-item">Historical Analysis</div>
          <div className="nav-item">API</div>
        </nav>

        <div className="sidebar-bottom">
          <div className="status-dot"></div>
          <span>ML Engine Online</span>
        </div>
      </aside>

      {/* MAIN */}
      <main className="main">

        {/* HEADER */}
        <header className="header">
          <div>
            <p className="eyebrow">AI-POWERED FORECAST MONITORING</p>
            <h1>Forecast Reliability Dashboard</h1>
            <p className="subtitle">
              Predicting where and when weather forecasts may become unreliable.
            </p>
          </div>

          <div className="day-selector">
            <label>Forecast Lead Day</label>
            <select
              value={leadDay}
              onChange={(e) => setLeadDay(Number(e.target.value))}
            >
              {Array.from({ length: 10 }, (_, i) => i + 1).map((day) => (
                <option key={day} value={day}>
                  Day {day}
                </option>
              ))}
            </select>
          </div>
        </header>

        {/* KPI CARDS */}
        <section className="kpi-grid">

          <div className="kpi-card">
            <span>Regions Monitored</span>
            <strong>{regions.length}</strong>
            <small>Across the prototype domain</small>
          </div>

          <div className="kpi-card">
            <span>Moderate / High Risk</span>
            <strong>
              {riskSummary.filter(
                (item) => item.risk !== "LOW"
              ).length}
            </strong>
            <small>Require attention</small>
          </div>

          <div className="kpi-card">
            <span>Average Confidence</span>
            <strong>
              {riskSummary.length
                ? Math.round(
                    (riskSummary.reduce(
                      (sum, item) => sum + item.confidence,
                      0
                    ) /
                      riskSummary.length) *
                      100
                  )
                : 0}
              %
            </strong>
            <small>For Day {leadDay}</small>
          </div>

          <div className="kpi-card">
            <span>Current Lead Day</span>
            <strong>D{leadDay}</strong>
            <small>Forecast horizon</small>
          </div>

        </section>

        {/* CONTENT GRID */}
        <section className="content-grid">

          {/* REGION RISK PANEL */}
          <div className="panel region-panel">
            <div className="panel-header">
              <div>
                <p className="panel-label">REGION-WISE RISK</p>
                <h2>Forecast Reliability</h2>
              </div>
              <span className="live-badge">LIVE</span>
            </div>

            <div className="region-list">
              {riskSummary.map((item) => (
                <button
                  key={item.region}
                  className={`region-row ${
                    selectedRegion === item.region ? "selected" : ""
                  }`}
                  onClick={() => setSelectedRegion(item.region)}
                >
                  <div className="region-name">
                    <span
                      className={`risk-dot ${getRiskClass(item.risk)}`}
                    ></span>
                    {item.region}
                  </div>

                  <div className="region-confidence">
                    {Math.round(item.confidence * 100)}%
                  </div>

                  <div
                    className={`risk-pill ${getRiskClass(item.risk)}`}
                  >
                    {item.risk}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* SELECTED REGION */}
          <div className="panel detail-panel">

            <div className="panel-header">
              <div>
                <p className="panel-label">SELECTED REGION</p>
                <h2>{selectedRegion}</h2>
              </div>
            </div>

            {prediction && (
              <>
                <div className="main-confidence">
                  <div className="confidence-circle">
                    <span>
                      {Math.round(prediction.confidence * 100)}%
                    </span>
                    <small>Confidence</small>
                  </div>

                  <div className="prediction-summary">
                    <span>Bust Probability</span>
                    <strong>
                      {Math.round(
                        prediction.bust_probability * 100
                      )}
                      %
                    </strong>

                    <div
                      className={`risk-pill ${getRiskClass(
                        prediction.risk
                      )}`}
                    >
                      {prediction.risk} RISK
                    </div>
                  </div>
                </div>

                <div className="metrics">

                  <div className="metric">
                    <span>Rainfall Forecast</span>
                    <strong>
                      {prediction.rainfall_forecast} mm
                    </strong>
                  </div>

                  <div className="metric">
                    <span>Previous Forecast</span>
                    <strong>
                      {prediction.previous_forecast} mm
                    </strong>
                  </div>

                  <div className="metric">
                    <span>Forecast Revision</span>
                    <strong>
                      {prediction.forecast_revision} mm
                    </strong>
                  </div>

                  <div className="metric">
                    <span>Historical MAE</span>
                    <strong>
                      {prediction.historical_mae}
                    </strong>
                  </div>

                </div>

                <div className="stability">
                  <div className="stability-header">
                    <span>Forecast Stability</span>
                    <strong>
                      {prediction.stability_index}
                    </strong>
                  </div>

                  <div className="progress">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${Math.min(
                          prediction.stability_index * 100,
                          100
                        )}%`,
                      }}
                    ></div>
                  </div>
                </div>
              </>
            )}

          </div>

        </section>

        {/* EXPLANATION */}
        <section className="panel explanation-panel">
          <div className="panel-header">
            <div>
              <p className="panel-label">MODEL INTERPRETATION</p>
              <h2>Why should we trust this forecast?</h2>
            </div>
          </div>

          <div className="explanation-grid">

            <div className="reason">
              <div className="reason-number">01</div>
              <div>
                <h3>Historical Error</h3>
                <p>
                  The model considers how large forecast errors
                  have been historically.
                </p>
              </div>
            </div>

            <div className="reason">
              <div className="reason-number">02</div>
              <div>
                <h3>Forecast Lead Time</h3>
                <p>
                  Longer forecast horizons can introduce greater
                  uncertainty.
                </p>
              </div>
            </div>

            <div className="reason">
              <div className="reason-number">03</div>
              <div>
                <h3>Weather Variability</h3>
                <p>
                  Rapidly changing conditions can reduce forecast
                  reliability.
                </p>
              </div>
            </div>

          </div>
        </section>

      </main>
    </div>
  );
}

export default App;