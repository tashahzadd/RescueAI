import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";

function formatDetails(details) {
  if (!details || Object.keys(details).length === 0) {
    return "-";
  }

  if ("severity" in details) {
    return `Severity: ${details.severity}`;
  }

  if ("conflicting_info" in details) {
    return `Conflicting information: ${details.conflicting_info ? "Yes" : "No"}`;
  }

  if ("plan_id" in details) {
    return `Plan ID: ${String(details.plan_id).slice(0, 8)}...`;
  }

  return Object.entries(details)
    .map(([key, value]) => {
      const label = key
        .replaceAll("_", " ")
        .replace(/\b\w/g, (char) => char.toUpperCase());

      return `${label}: ${String(value)}`;
    })
    .join(" | ");
}

function formatAction(action) {
  return action
    ? action
        .replaceAll("_", " ")
        .toLowerCase()
        .replace(/\b\w/g, (char) => char.toUpperCase())
    : "-";
}

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listAuditLogs()
      .then(setLogs)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-header">
        <h2>Audit Logs</h2>
      </div>

      {loading && <p className="muted">Loading audit logs...</p>}

      <div className="section-card" style={{ overflowX: "auto" }}>
        <table
          className="data-table"
          style={{
            width: "100%",
            minWidth: "900px",
            tableLayout: "auto",
          }}
        >
          <thead>
            <tr>
              <th style={{ minWidth: "180px" }}>Time</th>
              <th style={{ minWidth: "170px" }}>Actor</th>
              <th style={{ minWidth: "220px" }}>Action</th>
              <th style={{ minWidth: "100px" }}>Incident</th>
              <th style={{ minWidth: "260px" }}>Details</th>
            </tr>
          </thead>

          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.created_at).toLocaleString()}</td>

                <td>{log.actor || "-"}</td>

                <td>
                  <span className="audit-action">
                    {formatAction(log.action)}
                  </span>
                </td>

                <td>
                  {log.incident_id
                    ? log.incident_id.slice(0, 8)
                    : "-"}
                </td>

                <td className="muted small">
                  {formatDetails(log.details)}
                </td>
              </tr>
            ))}

            {logs.length === 0 && !loading && (
              <tr>
                <td colSpan={5} className="muted">
                  No audit events yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
