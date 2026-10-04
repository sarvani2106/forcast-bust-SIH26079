import Header from "../components/layout/Header";

const endpoints = [
  { path: "/real/prediction", purpose: "Model prediction for the nearest available grid point and requested lead day.", params: "latitude, longitude, lead_day (1–10)", fields: "forecast_date, latitude, longitude, lead_day, rainfall_forecast, previous_forecast, forecast_revision, historical_mae, bust_probability, confidence, risk, forecast_stability" },
  { path: "/real/forecast", purpose: "Day 1–10 forecast and model output for the nearest grid point.", params: "latitude, longitude", fields: "forecast_days[]: forecast_date, latitude, longitude, lead_day, rainfall_forecast, previous_forecast, forecast_revision, historical_mae, forecast_stability, bust_probability, confidence, risk" },
  { path: "/real/risk-map", purpose: "Grid-level bust risk across the available forecast domain.", params: "lead_day (1–10)", fields: "forecast_date, lead_day, total_points, points[]: latitude, longitude, rainfall_forecast, forecast_revision, historical_mae, forecast_stability, bust_probability, confidence, risk, bust_prediction" },
  { path: "/explain/{region}", purpose: "SHAP factors for a region and lead day (legacy region-based model endpoint).", params: "region (path), lead_day (1–10)", fields: "region, lead_day, bust_probability, confidence, risk, top_factors[]: feature, value, shap_impact, direction, explanation" },
  { path: "/trend/{region}", purpose: "Historical forecast observations for the selected region and lead day.", params: "region (path), lead_day (1–10)", fields: "trend[]: forecast_date, rainfall_forecast, forecast_revision, stability_index, bust_probability, risk" },
];

function ApiReference() {
  return <div className="api-reference-page">
    <Header title="API Reference" description="Forecast reliability service endpoints" context="GET · JSON" />
    <section className="api-reference-intro"><p>Real grid-level endpoints power the forecast views. Base URL is configured through <code>VITE_API_BASE_URL</code>.</p></section>
    <div className="api-reference-sections">{endpoints.map((endpoint) => <article className="api-endpoint-card" key={endpoint.path}>
      <div className="api-endpoint-heading"><span className="api-method-badge">GET</span><code className="api-endpoint-path">{endpoint.path}</code></div>
      <p className="api-endpoint-purpose">{endpoint.purpose}</p>
      <div className="api-detail-block"><h4>Parameters</h4><code>{endpoint.params}</code></div>
      <div className="api-detail-block"><h4>Response fields</h4><p className="api-response-fields">{endpoint.fields}</p></div>
    </article>)}</div>
  </div>;
}
export default ApiReference;
