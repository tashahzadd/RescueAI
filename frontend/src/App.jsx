import React, { useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import Incidents from "./pages/Incidents.jsx";
import IncidentDetail from "./pages/IncidentDetail.jsx";
import Resources from "./pages/Resources.jsx";
import Hospitals from "./pages/Hospitals.jsx";
import MapPage from "./pages/MapPage.jsx";
import Analytics from "./pages/Analytics.jsx";
import Notifications from "./pages/Notifications.jsx";
import AuditLogs from "./pages/AuditLogs.jsx";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "🖥" },
  { id: "incidents", label: "Incidents", icon: "🚨" },
  { id: "map", label: "Resource Map", icon: "🗺" },
  { id: "resources", label: "Resources", icon: "🚑" },
  { id: "hospitals", label: "Hospitals", icon: "🏥" },
  { id: "analytics", label: "Analytics", icon: "📊" },
  { id: "notifications", label: "Notifications", icon: "🔔" },
  { id: "audit", label: "Audit Logs", icon: "📋" },
];

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);

  const openIncident = (id) => {
    setSelectedIncidentId(id);
    setPage("incident-detail");
  };

  const navigate = (id) => {
    setSelectedIncidentId(null);
    setPage(id);
  };

  const renderPage = () => {
    switch (page) {
      case "dashboard":
        return <Dashboard onOpenIncident={openIncident} onNavigate={navigate} />;
      case "incidents":
        return <Incidents onOpenIncident={openIncident} />;
      case "incident-detail":
        return <IncidentDetail incidentId={selectedIncidentId} onBack={() => navigate("incidents")} />;
      case "map":
        return <MapPage />;
      case "resources":
        return <Resources />;
      case "hospitals":
        return <Hospitals />;
      case "analytics":
        return <Analytics />;
      case "notifications":
        return <Notifications />;
      case "audit":
        return <AuditLogs />;
      default:
        return <Dashboard onOpenIncident={openIncident} onNavigate={navigate} />;
    }
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">🛟</span>
          <div>
            <div className="brand-title">RescueAI</div>
            <div className="brand-subtitle">Decision-Support Only</div>
          </div>
        </div>
        <nav>
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${page === item.id || (item.id === "incidents" && page === "incident-detail") ? "active" : ""}`}
              onClick={() => navigate(item.id)}
            >
              <span className="nav-icon">{item.icon}</span> {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <p>Demo/synthetic data only.<br />AI never dispatches autonomously - human approval required for every response plan.</p>
        </div>
      </aside>
      <main className="main-content">{renderPage()}</main>
    </div>
  );
}
