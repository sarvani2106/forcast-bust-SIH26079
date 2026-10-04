import { useCallback, useEffect, useMemo, useState } from "react";
import { getRiskMap, summarizeRiskMap } from "../api/dashboardApi";
import { getForecast, getPrediction } from "../api/forecastApi";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import RiskBadge from "../components/common/RiskBadge";
import RiskMap from "../components/dashboard/RiskMap";
import Header from "../components/layout/Header";

const fmt = (value, digits = 2) => value == null ? "No data" : Number(value).toLocaleString("en", { maximumFractionDigits: digits });
const pct = (value) => value == null ? "No data" : `${(Number(value) * 100).toFixed(1)}%`;

function Dashboard() {
  const [leadDay, setLeadDay] = useState(5);
  const [riskMap, setRiskMap] = useState(null);
  const [mapState, setMapState] = useState("loading");
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [detailState, setDetailState] = useState("idle");
  const summary = useMemo(() => summarizeRiskMap(riskMap), [riskMap]);
  const handlePointSelect = useCallback((point) => {
    setDetailState("loading");
    setSelectedPoint({ ...point });
  }, []);
  const handleLeadDayChange = (event) => {
    setMapState("loading");
    if (selectedPoint) setDetailState("loading");
    setLeadDay(Number(event.target.value));
  };

  useEffect(() => {
    let current = true;
    getRiskMap(leadDay).then((data) => {
      if (!current) return;
      setRiskMap(data);
      setMapState("ready");
    }).catch(() => current && setMapState("error"));
    return () => { current = false; };
  }, [leadDay]);

  useEffect(() => {
    if (!selectedPoint) return undefined;
    let current = true;
    Promise.all([
      getPrediction(selectedPoint.latitude, selectedPoint.longitude, leadDay),
      getForecast(selectedPoint.latitude, selectedPoint.longitude),
    ]).then(([point, outlook]) => {
      if (!current) return;
      setPrediction(point);
      setForecast(outlook);
      setDetailState("ready");
    }).catch(() => current && setDetailState("error"));
    return () => { current = false; };
  }, [leadDay, selectedPoint]);

  return <div className="dashboard-page">
    <Header title="Forecast Reliability" description="Grid-level forecast bust risk across India" context="Historical NCMRWF Forecast Data · NCMRWF TIGGE + IMD rainfall verification" />
    <section className="dashboard-control-bar">
      <div><span className="dashboard-kicker">Forecast horizon</span><strong>Inspect reliability by lead day</strong></div>
      <label className="dashboard-select-label"><span>Lead Day</span><select value={leadDay} onChange={handleLeadDayChange}>{Array.from({ length: 10 }, (_, i) => <option key={i + 1} value={i + 1}>Day {i + 1}</option>)}</select></label>
    </section>
    {mapState === "loading" && <LoadingState />}
    {mapState === "error" && <ErrorState message="Unable to load forecast data." onRetry={() => { setMapState("loading"); getRiskMap(leadDay).then((data) => { setRiskMap(data); setMapState("ready"); }).catch(() => setMapState("error")); }} />}
    {mapState === "ready" && <>
      <section className="dashboard-summary-section">
        <div className="dashboard-section-heading"><div><span className="dashboard-kicker">Day {leadDay} · {riskMap?.forecast_date ?? "No data"}</span><h2>Forecast Reliability Summary</h2></div><span className="dashboard-lead-indicator">{summary.total_points ?? 0} grid points</span></div>
        <div className="dashboard-summary-grid">
          <Metric label="Grid points" value={summary.total_points ?? "No data"} />
          <Metric label="High risk" value={summary.high_risk_count ?? "No data"} tone="is-high" />
          <Metric label="Moderate risk" value={summary.moderate_risk_count ?? "No data"} tone="is-moderate" />
          <Metric label="Low risk" value={summary.low_risk_count ?? "No data"} tone="is-low" />
          <Metric label="Mean bust probability" value={pct(summary.average_bust_probability)} />
        </div>
      </section>
      <section className="dashboard-map-section">
        <div className="dashboard-section-heading"><div><span className="dashboard-kicker">Geographic intelligence</span><h2>Forecast Bust Risk Map</h2><p>Grid-level forecast reliability across India</p></div><span className="dashboard-lead-indicator">Day {leadDay} · {riskMap?.forecast_date ?? "No data"}</span></div>
        <RiskMap riskMap={riskMap} leadDay={leadDay} onSelectPoint={handlePointSelect} />
      </section>
      <section className="dashboard-panel outlook-panel">
        <div className="dashboard-panel-header"><div><span className="dashboard-kicker">Selected grid point</span><h2>{selectedPoint ? `${Number(selectedPoint.latitude).toFixed(2)}°, ${Number(selectedPoint.longitude).toFixed(2)}°` : "Select a map point"}</h2></div></div>
        {!selectedPoint && <EmptyState message="Select a grid point on the map to inspect its prediction and 10-day outlook." />}
        {detailState === "loading" && <LoadingState />}
        {detailState === "error" && <ErrorState message="Unable to load forecast data." />}
        {detailState === "ready" && prediction && <>
          <div className="selected-point-summary"><Metric label="Risk · Day " value={<RiskBadge risk={prediction.risk} />} /><Metric label="Bust probability" value={pct(prediction.bust_probability)} /><Metric label="Confidence" value={pct(prediction.confidence)} /><Metric label="Rainfall forecast" value={`${fmt(prediction.rainfall_forecast)} mm`} /></div>
          {forecast?.forecast_days?.length ? <div className="horizon-strip">{forecast.forecast_days.map((day) => <div className={`horizon-day ${day.lead_day === leadDay ? "is-selected" : ""}`} key={day.lead_day}><span>Day {day.lead_day}</span><strong>{pct(day.bust_probability)}</strong><RiskBadge risk={day.risk} /></div>)}</div> : <EmptyState message="No forecast data available for this selection." />}
        </>}
      </section>
    </>}
  </div>;
}

function Metric({ label, value, tone = "" }) { return <article className="dashboard-metric"><span className="dashboard-metric-label">{label}</span><strong className={`dashboard-metric-value ${tone}`}>{value}</strong></article>; }
export default Dashboard;
