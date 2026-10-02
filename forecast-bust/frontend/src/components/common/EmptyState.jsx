import { Inbox } from "lucide-react";

function EmptyState({ message = "No data available." }) {
  return (
    <section
      className="empty-state"
      aria-live="polite"
      style={{
        display: "grid",
        placeItems: "center",
        gap: "var(--space-2)",
        minHeight: "180px",
        padding: "var(--space-6)",
        border: "1px dashed var(--color-border)",
        borderRadius: "var(--radius-md)",
        color: "var(--color-text-muted)",
        textAlign: "center",
      }}
    >
      <Inbox aria-hidden="true" focusable="false" size={20} />
      <p style={{ margin: 0, color: "inherit" }}>{message}</p>
    </section>
  );
}

export default EmptyState;
