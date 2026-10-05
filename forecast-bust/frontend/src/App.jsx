import { BrowserRouter, Outlet, Route, Routes } from "react-router-dom";
import PageContainer from "./components/layout/PageContainer";
import Sidebar from "./components/layout/Sidebar";
import Dashboard from "./pages/Dashboard";
import ForecastAnalysis from "./pages/ForecastAnalysis";
import HistoricalPerformance from "./pages/HistoricalPerformance";
import Explainability from "./pages/Explainability";
import "./App.css";

function AppShell() {
  return (
    <div className="app-shell">
      <Sidebar />

      <div className="main-content">
        <PageContainer>
          <Outlet />
        </PageContainer>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/forecast" element={<ForecastAnalysis />} />
          <Route path="/historical" element={<HistoricalPerformance />} />
          <Route path="/explainability" element={<Explainability />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;