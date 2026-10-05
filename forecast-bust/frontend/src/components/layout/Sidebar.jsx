import {
  Activity,
  BrainCircuit,
  CloudSun,
  History,
  LayoutDashboard,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const navigationItems = [
  { label: "Dashboard", to: "/", icon: LayoutDashboard, end: true },
  { label: "Forecast Analysis", to: "/forecast", icon: Activity },
  {
    label: "Historical Performance",
    to: "/historical",
    icon: History,
  },
  { label: "Explainability", to: "/explainability", icon: BrainCircuit },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-branding">
        <span className="sidebar-brand-icon">
          <CloudSun aria-hidden="true" focusable="false" />
        </span>
        <div className="sidebar-brand-copy">
          <strong>Forecast AI</strong>
          <span>Forecast Reliability Engine</span>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Primary navigation">
        {navigationItems.map(({ label, to, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end}>
            <Icon aria-hidden="true" focusable="false" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;
