import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";
import SeverityBadge from "../components/SeverityBadge.jsx";

export default function Incidents({ onOpenIncident }) {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ raw_text: "", source_type: "CITIZEN", location: "" });
  const [submitting, setSubmitting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      setIncidents(await api.listIncidents());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.raw_text.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const incident = await api.createIncident(form);
      setForm({ raw_text: "", source_type: "CITIZEN", location: "" });
      setShowForm(false);
      await load();
      onOpenIncident(incident.id);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>Incidents</h2>
        <button className="btn btn-primary" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Cancel" : "+ New Emergency Report"}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {showForm && (
        <form className="section-card" onSubmit={submit}>
          <label className="field-label">Raw emergency report text</label>
          <textarea
            className="text-area"
            rows={4}
            value={form.raw_text}
            onChange={(e) => setForm({ ...form, raw_text: e.target.value })}
            placeholder="e.g. Heavy flooding reported on Shahrah-e-Faisal, several cars stranded, water rising..."
            required
          />
          <div className="form-row">
            <div>
              <label className="field-label">Source type</label>
              <select
                className="select-input"
                value={form.source_type}
                onChange={(e) => setForm({ ...form, source_type: e.target.value })}
              >
                <option value="FIELD_OFFICER">Field Officer</option>
                <option value="VERIFIED_ORG">Verified Organization</option>
                <option value="EMERGENCY_OPERATOR">Emergency Operator</option>
                <option value="CITIZEN">Citizen Report</option>
                <option value="SOCIAL_MEDIA">Unverified Social Media</option>
              </select>
            </div>
            <div>
              <label className="field-label">Location (optional)</label>
              <input
                className="text-input"
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                placeholder="e.g. Shahrah-e-Faisal, Karachi"
              />
            </div>
          </div>
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Submitting to AI Intake Agent..." : "Submit Report"}
          </button>
        </form>
      )}

      <div className="section-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Location</th>
              <th>Est. Victims</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Conflicting?</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((inc) => (
              <tr key={inc.id}>
                <td>{inc.incident_type}</td>
                <td>{inc.location}</td>
                <td>
                  {inc.estimated_victims_min != null
                    ? inc.estimated_victims_min === inc.estimated_victims_max
                      ? inc.estimated_victims_max
                      : `${inc.estimated_victims_min}-${inc.estimated_victims_max}`
                    : "Unknown"}
                </td>
                <td><SeverityBadge severity={inc.severity} /></td>
                <td>{inc.status}</td>
                <td>{inc.conflicting_info ? <span className="conflict-tag">⚠ Yes</span> : "No"}</td>
                <td><button className="btn-link" onClick={() => onOpenIncident(inc.id)}>View →</button></td>
              </tr>
            ))}
            {incidents.length === 0 && !loading && (
              <tr><td colSpan={7} className="muted">No incidents reported yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
