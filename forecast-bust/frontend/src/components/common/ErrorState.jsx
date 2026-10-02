import { AlertCircle } from "lucide-react";

function ErrorState({ message = "Unable to load data." }) {
  return (
    <div
      className="error-state"
      role="alert"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "var(--space-2)",
        padding: "var(--space-6)",
        color: "var(--color-risk-high)",
        textAlign: "center",
      }}
    >
      <AlertCircle aria-hidden="true" focusable="false" size={18} />
      <p style={{ margin: 0, color: "inherit" }}>{message}</p>
    </div>
  );
}

export default ErrorState;
