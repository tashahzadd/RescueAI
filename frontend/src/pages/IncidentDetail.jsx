import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";
import SeverityBadge from "../components/SeverityBadge.jsx";
import ResponsePlanPanel from "../components/ResponsePlanPanel.jsx";

export default function IncidentDetail({ incidentId, onBack }) {
  const [incident, setIncident] = useState(null);
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [newReportText, setNewReportText] = useState("");
  const [newReportSource, setNewReportSource] = useState("CITIZEN");

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const inc = await api.getIncident(incidentId);
      setIncident(inc);
      try {
        const p = await api.getResponsePlan(incidentId);
        setPlan(p);
      } catch (e) {
        setPlan(null); // no plan yet - not an error
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incidentId]);

  const runAnalysis = async () => {
    setAnalyzing(true);
    setError(null);
    try {
      const p = await api.analyzeIncident(incidentId);
      setPlan(p);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const addReport = async (e) => {
    e.preventDefault();
    if (!newReportText.trim()) return;
    setBusy(true);
    try {
      await api.addReport(incidentId, { raw_text: newReportText, source_type: newReportSource });
      setNewReportText("");
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const approve = async (approverName) => {
    setBusy(true);
    setError(null);
    try {
      const p = await api.approveResponse(incidentId, { approved_by: approverName });
      setPlan(p);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const reject = async (approverName, reason) => {
    setBusy(true);
    setError(null);
    try {
      const p = await api.rejectResponse(incidentId, { rejected_by: approverName, reason });
      setPlan(p);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const resolve = async () => {
    setBusy(true);
    try {
      await api.resolveIncident(incidentId);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  if (loading && !incident) return <p className="muted">Loading incident...</p>;
  if (!incident) return <p className="alert alert-error">Incident not found.</p>;

  return (
    <div>
      <button className="btn-link" onClick={onBack}>← Back</button>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="page-header">
        <h2>{incident.incident_type} - {incident.location}</h2>
        <SeverityBadge severity={incident.severity} />
      </div>

      <div className="incident-meta-grid">
        <div><span className="muted">Status</span><div>{incident.status}</div></div>
        <div><span className="muted">Estimated Victims</span><div>
          {incident.estimated_victims_min != null
            ? (incident.estimated_victims_min === incident.estimated_victims_max
                ? incident.estimated_victims_max
                : `${incident.estimated_victims_min}-${incident.estimated_victims_max}`)
            : "Unknown"}
        </div></div>
        <div><span className="muted">Hazards</span><div>{incident.hazards?.join(", ") || "None reported"}</div></div>
        <div><span className="muted">Reported</span><div>{new Date(incident.created_at).toLocaleString()}</div></div>
      </div>

      {incident.conflicting_info && (
        <div className="alert alert-warning">
          <strong>CONFLICTING INFORMATION DETECTED</strong>
          <p>{incident.conflict_notes}</p>
        </div>
      )}

      <div className="section-card">
        <h3>Reports ({incident.reports?.length || 0})</h3>
        <table className="data-table">
          <thead><tr><th>Text</th><th>Source</th><th>Reliability</th><th>Extracted Victims</th></tr></thead>
          <tbody>
            {incident.reports?.map((r) => (
              <tr key={r.id}>
                <td>{r.raw_text}</td>
                <td>{r.source_type}</td>
                <td>
                  <span className={`reliability-tag reliability-${r.reliability.toLowerCase()}`}>{r.reliability}</span>
                </td>
                <td>{r.extracted_victims ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <form className="add-report-form" onSubmit={addReport}>
          <input
            className="text-input"
            value={newReportText}
            onChange={(e) => setNewReportText(e.target.value)}
            placeholder="Add another report (e.g. conflicting eyewitness account)..."
          />
          <select className="select-input" value={newReportSource} onChange={(e) => setNewReportSource(e.target.value)}>
            <option value="FIELD_OFFICER">Field Officer</option>
            <option value="VERIFIED_ORG">Verified Org</option>
            <option value="EMERGENCY_OPERATOR">Emergency Operator</option>
            <option value="CITIZEN">Citizen</option>
            <option value="SOCIAL_MEDIA">Social Media</option>
          </select>
          <button className="btn" type="submit" disabled={busy}>Add Report</button>
        </form>
      </div>

      {!plan && (
        <div className="section-card center-cta">
          <p>No AI response plan generated yet.</p>
          <button className="btn btn-primary" onClick={runAnalysis} disabled={analyzing}>
            {analyzing ? "Running AI Agents (Analysis → Risk → Resources → Hospital → Planning)..." : "Run AI Analysis"}
          </button>
        </div>
      )}

      {plan && (
        <div className="section-card">
          <ResponsePlanPanel plan={plan} onApprove={approve} onReject={reject} busy={busy} />
          {plan.approval_status === "APPROVED" && incident.status === "DISPATCHED" && (
            <button className="btn" style={{ marginTop: 12 }} onClick={resolve} disabled={busy}>
              Mark Incident Resolved
            </button>
          )}
        </div>
      )}
    </div>
  );
}
