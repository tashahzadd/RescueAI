import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listAuditLogs().then(setLogs).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-header"><h2>Audit Logs</h2></div>
      {loading && <p className="muted">Loading audit logs...</p>}
      <div className="section-card">
        <table className="data-table">
          <thead>
            <tr><th>Time</th><th>Actor</th><th>Action</th><th>Incident</th><th>Details</th></tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id}>
                <td>{new Date(l.created_at).toLocaleString()}</td>
                <td>{l.actor}</td>
                <td><span className="audit-action">{l.action}</span></td>
                <td>{l.incident_id ? l.incident_id.slice(0, 8) : "-"}</td>
                <td className="muted small">{JSON.stringify(l.details)}</td>
              </tr>
            ))}
            {logs.length === 0 && !loading && (
              <tr><td colSpan={5} className="muted">No audit events yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
