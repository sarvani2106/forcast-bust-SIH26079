function Header({ title = "Forecast Reliability Engine", description = "AI-based medium-range forecast bust detection", context = "Historical NCMRWF Forecast Data" }) {
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
          {description}
        </p>
      </div>
      {context && <span className="header-context">{context}</span>}
    </header>
  );
}

export default Header;
