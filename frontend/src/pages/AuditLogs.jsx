import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";

function formatAction(action) {
  return action
    ? action
        .replaceAll("_", " ")
        .toLowerCase()
        .replace(/\b\w/g, (char) => char.toUpperCase())
    : "-";
}

function formatDetails(action, details) {
  if (!details || Object.keys(details).length === 0) {
    if (action === "INCIDENT_RESOLVED") {
      return "Incident marked as resolved";
    }

    return "-";
  }

  switch (action) {
    case "INCIDENT_CREATED":
      return details.incident_type
        ? `Incident created: ${details.incident_type}`
        : "New incident created";

    case "REPORT_ADDED":
      return `Conflicting information: ${
        details.conflicting_info ? "Yes" : "No"
      }`;

    case "AI_ANALYSIS_COMPLETE":
      return details.severity
        ? `AI assessment completed - Severity: ${details.severity}`
        : "AI assessment completed";

    case "RESPONSE_PLAN_GENERATED":
      return "AI response plan generated";

    case "RESPONSE_APPROVED":
      return "Response plan approved by commander";

    case "RESPONSE_REJECTED":
      return details.reason
        ? `Response plan rejected - Reason: ${details.reason}`
        : "Response plan rejected";

    case "SIMULATED_DISPATCH":
      return "Approved resources assigned in simulation";

    case "INCIDENT_RESOLVED":
      return "Incident marked as resolved";

    default:
      break;
  }

  if ("severity" in details) {
    return `Severity: ${details.severity}`;
  }

  if ("conflicting_info" in details) {
    return `Conflicting information: ${
      details.conflicting_info ? "Yes" : "No"
    }`;
  }

  if ("plan_id" in details) {
    return "Response plan activity recorded";
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
            minWidth: "950px",
            tableLayout: "auto",
          }}
        >
          <thead>
            <tr>
              <th style={{ minWidth: "180px" }}>Time</th>
              <th style={{ minWidth: "170px" }}>Actor</th>
              <th style={{ minWidth: "220px" }}>Action</th>
              <th style={{ minWidth: "100px" }}>Incident</th>
              <th style={{ minWidth: "300px" }}>Details</th>
            </tr>
          </thead>

          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.created_at).toLocaleString()}</td>

                <td>
                  {log.actor === "AI_SYSTEM"
                    ? "AI System"
                    : log.actor === "SYSTEM"
                    ? "System"
                    : log.actor || "-"}
                </td>

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
                  {formatDetails(log.action, log.details)}
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
