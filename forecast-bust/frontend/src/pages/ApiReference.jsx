import Header from "../components/layout/Header";

const endpointSections = [
  {
    title: "System",
    endpoints: [
      {
        path: "/",
        purpose: "Backend health/status.",
        responseFields: ["status", "database", "model"],
      },
      {
        path: "/regions",
        purpose: "Get available forecast regions.",
        responseFields: [],
      },
    ],
  },
  {
    title: "Forecast",
    endpoints: [
      {
        path: "/prediction/{region}",
        purpose: "Get forecast bust prediction for a selected region and lead day.",
        parameters: [
          "region (path parameter)",
          "lead_day (query parameter, 1–10)",
        ],
        responseFields: [
          "region",
          "lead_day",
          "rainfall_forecast",
          "previous_forecast",
          "forecast_revision",
          "historical_mae",
          "bust_probability",
          "confidence",
          "risk",
          "stability_index",
        ],
      },
      {
        path: "/forecast/{region}",
        purpose: "Get forecast reliability information for lead days 1–10.",
        parameters: ["region (path parameter)"],
        responseFields: [
          "lead_day",
          "rainfall_forecast",
          "bust_probability",
          "confidence",
          "risk",
          "stability_index",
        ],
      },
    ],
  },
  {
    title: "Risk & Dashboard",
    endpoints: [
      {
        path: "/risk-summary",
        purpose: "Get risk summary for the selected lead day.",
        parameters: ["lead_day (query parameter)"],
        responseFields: [],
      },
      {
        path: "/risk-map",
        purpose: "Get region-level risk information for map visualization.",
        parameters: ["lead_day (query parameter)"],
        responseFields: [
          "region",
          "lead_day",
          "rainfall_forecast",
          "bust_probability",
          "confidence",
          "risk",
          "stability_index",
          "weather_regime",
          "weather_variability",
          "historical_mae",
        ],
      },
      {
        path: "/dashboard-summary",
        purpose: "Get dashboard-level risk summary.",
        parameters: ["lead_day (query parameter)"],
        responseFields: [
          "lead_day",
          "total_regions",
          "high_risk_count",
          "moderate_risk_count",
          "low_risk_count",
          "average_bust_probability",
          "highest_risk_region",
          "highest_risk_probability",
        ],
      },
    ],
  },
  {
    title: "Analysis",
    endpoints: [
      {
        path: "/trend/{region}",
        purpose: "Get historical forecast trend for a region and lead day.",
        parameters: [
          "region (path parameter)",
          "lead_day (query parameter)",
        ],
        responseFields: [
          "trend[]",
          "forecast_date",
          "rainfall_forecast",
          "forecast_revision",
          "stability_index",
          "bust_probability",
          "risk",
        ],
      },
      {
        path: "/forecast-evolution/{region}",
        title: "Forecast Revision & Stability",
        purpose: "Get historical forecast evolution, revision, and stability information for a region.",
        parameters: [
          "region (path parameter)",
          "lead_day (query parameter)",
        ],
        responseFields: [
          "forecast_date",
          "rainfall_forecast",
          "previous_forecast",
          "revision",
          "stability_index",
        ],
      },
      {
        path: "/explain/{region}",
        purpose: "Get model/SHAP explanation for a region and lead day.",
        parameters: [
          "region (path parameter)",
          "lead_day (query parameter)",
        ],
        responseFields: [
          "region",
          "lead_day",
          "bust_probability",
          "risk",
          "top_factors[]",
          "feature",
          "impact",
          "explanation",
        ],
      },
    ],
  },
];

function EndpointCard({ endpoint }) {
  return (
    <article className="api-endpoint-card">
      <div className="api-endpoint-heading">
        <span className="api-method-badge">GET</span>
        <code className="api-endpoint-path">{endpoint.path}</code>
      </div>

      {endpoint.title && <h3 className="api-endpoint-title">{endpoint.title}</h3>}
      <p className="api-endpoint-purpose">{endpoint.purpose}</p>

      {endpoint.parameters?.length ? (
        <div className="api-detail-block">
          <h4>Parameters</h4>
          <ul className="api-parameter-list">
            {endpoint.parameters.map((parameter) => (
              <li key={parameter}>
                <code>{parameter}</code>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {endpoint.responseFields.length ? (
        <div className="api-detail-block">
          <h4>Response</h4>
          <div className="api-field-list">
            {endpoint.responseFields.map((field) => (
              <code key={field}>{field}</code>
            ))}
          </div>
        </div>
      ) : null}
    </article>
  );
}

function ApiReference() {
  return (
    <div className="api-reference-page">
      <Header title="API Reference" />

      <section className="api-reference-intro" aria-labelledby="api-reference-description">
        <div>
          <p id="api-reference-description">
            Backend endpoints provided by the Forecast Reliability Engine.
          </p>
          <div className="api-base-url-note">
            <span>Base URL</span>
            <code>Configured through VITE_API_BASE_URL</code>
          </div>
        </div>
      </section>

      <section className="api-overview-panel" aria-labelledby="api-overview-title">
        <span className="dashboard-kicker">API overview</span>
        <h2 id="api-overview-title">Forecast Reliability Engine</h2>
        <div className="api-overview-grid">
          <div>
            <span>API</span>
            <strong>Forecast Reliability Engine</strong>
          </div>
          <div>
            <span>Protocol</span>
            <strong>HTTP REST</strong>
          </div>
          <div>
            <span>Documentation</span>
            <strong>Available backend endpoints</strong>
          </div>
        </div>
      </section>

      <div className="api-reference-sections">
        {endpointSections.map((section) => (
          <section
            className="api-reference-section"
            key={section.title}
            aria-labelledby={`${section.title.toLowerCase().replaceAll(" ", "-")}-title`}
          >
            <div className="api-section-heading">
              <span className="dashboard-kicker">Endpoint group</span>
              <h2 id={`${section.title.toLowerCase().replaceAll(" ", "-")}-title`}>
                {section.title}
              </h2>
            </div>
            <div className="api-endpoint-grid">
              {section.endpoints.map((endpoint) => (
                <EndpointCard key={endpoint.path} endpoint={endpoint} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

export default ApiReference;