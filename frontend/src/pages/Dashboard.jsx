import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";
import StatCard from "../components/StatCard.jsx";
import SeverityBadge from "../components/SeverityBadge.jsx";

export default function Dashboard({ onOpenIncident, onNavigate }) {
  const [stats, setStats] = useState(null);
  const [recentIncidents, setRecentIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [demoLoading, setDemoLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, incidents] = await Promise.all([api.dashboardStats(), api.listIncidents()]);
      setStats(s);
      setRecentIncidents(incidents.slice(0, 8));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const runDemo = async () => {
    setDemoLoading(true);
    try {
      const res = await api.loadDemoScenario();
      await load();
      onOpenIncident(res.incident_id);
    } catch (e) {
      setError(e.message);
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>RescueAI Command Center</h2>
        <button className="btn btn-primary" onClick={runDemo} disabled={demoLoading}>
          {demoLoading ? "Loading demo scenario..." : "▶ Load Demo Incident"}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <p className="muted">Loading dashboard...</p>}

      {stats && (
        <div className="stat-grid">
          <StatCard label="Active Incidents" value={stats.active_incidents} />
          <StatCard label="Critical Incidents" value={stats.critical_incidents} accent="#dc2626" />
          <StatCard label="High Priority" value={stats.high_incidents} accent="#ea580c" />
          <StatCard label="Pending AI Recommendations" value={stats.pending_approvals} accent="#ca8a04" />
          <StatCard label="Ambulances Available" value={stats.ambulances_available} accent="#2563eb" />
          <StatCard label="Rescue Teams Available" value={stats.rescue_teams_available} accent="#16a34a" />
          <StatCard label="Fire Units Available" value={stats.fire_units_available} accent="#ea580c" />
          <StatCard label="Resolved Incidents" value={stats.resolved_incidents} accent="#64748b" />
        </div>
      )}

      <div className="section-card">
        <div className="section-header">
          <h3>Recent Incidents</h3>
          <button className="btn-link" onClick={() => onNavigate("incidents")}>View all →</button>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Location</th>
              <th>Severity</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {recentIncidents.map((inc) => (
              <tr key={inc.id}>
                <td>{inc.incident_type}</td>
                <td>{inc.location}</td>
                <td><SeverityBadge severity={inc.severity} /></td>
                <td>{inc.status}</td>
                <td><button className="btn-link" onClick={() => onOpenIncident(inc.id)}>View →</button></td>
              </tr>
            ))}
            {recentIncidents.length === 0 && !loading && (
              <tr><td colSpan={5} className="muted">No incidents yet. Try "Load Demo Incident" above.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
