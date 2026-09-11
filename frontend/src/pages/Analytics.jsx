import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import { api } from "../api/client.js";

const SEVERITY_COLORS = { CRITICAL: "#dc2626", HIGH: "#ea580c", MEDIUM: "#ca8a04", LOW: "#16a34a" };

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.dashboardAnalytics().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="muted">Loading analytics...</p>;
  if (!data) return <p className="alert alert-error">Could not load analytics.</p>;

  const byType = Object.entries(data.incidents_by_type || {}).map(([name, value]) => ({ name, value }));
  const bySeverity = Object.entries(data.incidents_by_severity || {}).map(([name, value]) => ({ name, value }));
  const resourceUtil = Object.entries(data.resource_utilization || {}).map(([name, v]) => ({
    name,
    total: v.total,
    dispatched: v.dispatched,
    available: v.total - v.dispatched,
  }));

  return (
    <div>
      <div className="page-header"><h2>Analytics</h2></div>

      <div className="stat-grid">
        <div className="stat-card"><div className="stat-value">{data.total_incidents}</div><div className="stat-label">Total Incidents</div></div>
        <div className="stat-card"><div className="stat-value">{data.resolved_incidents}</div><div className="stat-label">Resolved</div></div>
      </div>

      <div className="analytics-grid">
        <div className="section-card">
          <h3>Incidents by Type</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={byType}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#94a3b8" }} interval={0} angle={-20} textAnchor="end" height={70} />
              <YAxis tick={{ fill: "#94a3b8" }} allowDecimals={false} />
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }} />
              <Bar dataKey="value" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="section-card">
          <h3>Incidents by Severity</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={bySeverity} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                {bySeverity.map((entry) => (
                  <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] || "#64748b"} />
                ))}
              </Pie>
              <Legend />
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="section-card" style={{ gridColumn: "1 / -1" }}>
          <h3>Resource Utilization</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={resourceUtil}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#94a3b8" }} interval={0} angle={-20} textAnchor="end" height={80} />
              <YAxis tick={{ fill: "#94a3b8" }} allowDecimals={false} />
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }} />
              <Legend />
              <Bar dataKey="available" stackId="a" fill="#16a34a" name="Available" />
              <Bar dataKey="dispatched" stackId="a" fill="#dc2626" name="Dispatched" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
