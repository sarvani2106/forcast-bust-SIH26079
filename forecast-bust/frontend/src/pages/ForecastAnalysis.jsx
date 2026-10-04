import { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import { CategoryScale, Chart as ChartJS, Filler, LinearScale, LineElement, PointElement, Tooltip } from "chart.js";
import { getForecast, getPrediction } from "../api/forecastApi";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import RiskBadge from "../components/common/RiskBadge";
import Header from "../components/layout/Header";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);
const days = Array.from({ length: 10 }, (_, i) => i + 1);
const fmt = (value, digits = 2) => value == null ? "No data" : Number(value).toLocaleString("en", { maximumFractionDigits: digits });
const pct = (value) => value == null ? "No data" : `${(Number(value) * 100).toFixed(1)}%`;

export default function ForecastAnalysis() {
  const [coords, setCoords] = useState({ latitude: "22.5", longitude: "79" });
  const [leadDay, setLeadDay] = useState(5);
  const [data, setData] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [state, setState] = useState("loading");
  const load = (point = coords, day = leadDay) => {
    setState("loading");
    Promise.all([getForecast(Number(point.latitude), Number(point.longitude)), getPrediction(Number(point.latitude), Number(point.longitude), day)])
      .then(([forecast, current]) => { setData(forecast); setPrediction(current); setState("ready"); })
      .catch(() => setState("error"));
  };
  useEffect(() => { load(); // initial real forecast request
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useEffect(() => { if (data) load(coords, leadDay); // lead-day selection refreshes real prediction
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leadDay]);
  const records = data?.forecast_days ?? [];
  const highest = records.reduce((max, day) => day.bust_probability > (max?.bust_probability ?? -Infinity) ? day : max, null);
  const chartData = { labels: records.map((item) => `Day ${item.lead_day}`), datasets: [{ label: "Bust probability", data: records.map((item) => item.bust_probability == null ? null : item.bust_probability * 100), borderColor: "#1677E8", backgroundColor: "rgba(22,119,232,.10)", fill: true, tension: 0.25, pointRadius: records.map((item) => item.lead_day === highest?.lead_day ? 6 : 3), pointBackgroundColor: records.map((item) => item.lead_day === highest?.lead_day ? "#E98B8B" : "#1677E8") }] };
  const options = { responsive: true, maintainAspectRatio: false, plugins: { tooltip: { callbacks: { label: (context) => `${context.parsed.y}%` } } }, scales: { y: { min: 0, max: 100, ticks: { callback: (value) => `${value}%` }, grid: { color: "#EAF1F7" } }, x: { grid: { display: false } } } };
  return <div className="forecast-analysis-page">
    <Header title="Forecast Analysis" description="10-day forecast reliability outlook" context="Historical NCMRWF Forecast Data" />
    <section className="forecast-analysis-controls">
      <div className="coordinate-controls"><label>Latitude<input type="number" step="0.01" value={coords.latitude} onChange={(event) => setCoords({ ...coords, latitude: event.target.value })} /></label><label>Longitude<input type="number" step="0.01" value={coords.longitude} onChange={(event) => setCoords({ ...coords, longitude: event.target.value })} /></label><button className="secondary-button" onClick={() => load()}>Load point</button></div>
      <div className="lead-day-selector" aria-label="Lead day">{days.map((day) => <button key={day} className={leadDay === day ? "is-selected" : ""} aria-pressed={leadDay === day} onClick={() => setLeadDay(day)}>Day {day}</button>)}</div>
    </section>
    {state === "loading" && <LoadingState />}{state === "error" && <ErrorState message="Unable to load forecast data." onRetry={() => load()} />}
    {state === "ready" && !records.length && <EmptyState message="No forecast data available for this selection." />}
    {state === "ready" && records.length > 0 && <>
      <section className="selected-forecast card"><div className="card-header"><div><span className="dashboard-kicker">Selected point · {prediction?.forecast_date ?? "No data"}</span><h2>Day {leadDay} reliability</h2></div><RiskBadge risk={prediction?.risk} /></div><div className="forecast-prediction-grid card-body">{[["Bust Probability", pct(prediction?.bust_probability)], ["Confidence", pct(prediction?.confidence)], ["Rainfall Forecast", `${fmt(prediction?.rainfall_forecast)} mm`], ["Forecast Revision", fmt(prediction?.forecast_revision)], ["Forecast Stability", fmt(prediction?.forecast_stability, 4)], ["Historical MAE", fmt(prediction?.historical_mae)]].map(([label, value]) => <div className="forecast-prediction-metric" key={label}><span className="forecast-prediction-label">{label}</span><strong>{value}</strong></div>)}</div></section>
      <section className="card forecast-chart-card"><div className="card-header"><div><span className="dashboard-kicker">10-day outlook</span><h2>Bust Probability vs Lead Day</h2></div>{highest && <span className="highest-risk-note">Highest returned probability · Day {highest.lead_day}</span>}</div><div className="forecast-chart-area"><Line data={chartData} options={options} /></div></section>
      <section className="card"><div className="card-header"><div><span className="dashboard-kicker">Backend forecast records</span><h2>Daily Reliability</h2></div></div><div className="forecast-table-wrap"><table className="forecast-reliability-table"><thead><tr>{["Lead Day", "Rainfall Forecast", "Bust Probability", "Confidence", "Risk", "Forecast Revision", "Forecast Stability", "Historical MAE"].map((x) => <th key={x}>{x}</th>)}</tr></thead><tbody>{records.map((day) => <tr key={day.lead_day} className={day.lead_day === highest?.lead_day ? "is-highest-risk" : ""}><td>Day {day.lead_day}</td><td>{fmt(day.rainfall_forecast)} mm</td><td>{pct(day.bust_probability)}</td><td>{pct(day.confidence)}</td><td><RiskBadge risk={day.risk} /></td><td>{fmt(day.forecast_revision)} mm</td><td>{fmt(day.forecast_stability, 4)}</td><td>{fmt(day.historical_mae)}</td></tr>)}</tbody></table></div></section>
    </>}
  </div>;
}
