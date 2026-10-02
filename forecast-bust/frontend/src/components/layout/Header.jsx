function Header({ title = "Forecast Reliability Engine" }) {
  return (
    <header
      className="app-header"
      style={{
        display: "flex",
        alignItems: "center",
        minHeight: "80px",
        padding: "var(--space-5) var(--space-6)",
        background: "var(--color-card-background)",
        borderBottom: "1px solid var(--color-border)",
      }}
    >
      <div>
        <h1
          style={{
            margin: 0,
            color: "var(--color-text-primary)",
            fontSize: "var(--font-size-page-title)",
          }}
        >
          {title}
        </h1>
        <p
          style={{
            margin: "var(--space-1) 0 0",
            color: "var(--color-text-secondary)",
            fontSize: "var(--font-size-secondary)",
          }}
        >
          AI-Based Medium-Range Forecast Bust Detection
        </p>
      </div>
    </header>
  );
}

export default Header;
