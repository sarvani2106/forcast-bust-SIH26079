const riskColors = {
  LOW: "var(--color-risk-low)",
  MODERATE: "var(--color-risk-moderate)",
  HIGH: "var(--color-risk-high)",
};

function RiskBadge({ risk }) {
  const isSupportedRisk = Object.prototype.hasOwnProperty.call(riskColors, risk);
  const label = isSupportedRisk ? risk : "Unknown";
  const color = isSupportedRisk ? riskColors[risk] : "var(--color-text-muted)";

  return (
    <span
      className="risk-badge"
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "28px",
        padding: "var(--space-1) var(--space-2)",
        border: `1px solid ${color}`,
        borderRadius: "var(--radius-sm)",
        color,
        fontSize: "var(--font-size-secondary)",
        fontWeight: 600,
        lineHeight: 1.2,
      }}
    >
      {label}
    </span>
  );
}

export default RiskBadge;
