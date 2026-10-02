import { LoaderCircle } from "lucide-react";

function LoadingState() {
  return (
    <div
      className="loading-state"
      role="status"
      aria-live="polite"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "var(--space-2)",
        padding: "var(--space-6)",
        color: "var(--color-text-muted)",
      }}
    >
      <LoaderCircle aria-hidden="true" focusable="false" size={18} />
      <span>Loading...</span>
    </div>
  );
}

export default LoadingState;
