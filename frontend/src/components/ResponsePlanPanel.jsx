import React, { useState } from "react";
import SeverityBadge from "./SeverityBadge.jsx";
import ConfidenceBar from "./ConfidenceBar.jsx";

export default function ResponsePlanPanel({ plan, onApprove, onReject, busy }) {
  const [approverName, setApproverName] = useState("Commander Amir Khan");
  const [rejectReason, setRejectReason] = useState("");
  const [showReject, setShowReject] = useState(false);

  if (!plan) return null;

  const hospital = plan.recommended_hospital?.recommended;
  const isPending = plan.approval_status === "PENDING";

  return (
    <div className="plan-panel">
      <div className="plan-header">
        <h3>AI Response Recommendation</h3>
        <SeverityBadge severity={plan.severity} />
      </div>

      <p className="plan-summary">{plan.summary}</p>

      <div className="plan-grid">
        <div className="plan-section">
          <h4>Recommended Resources</h4>
          <ul>
            {plan.recommended_resources?.map((rec) => (
              <li key={rec.resource_type}>
                <strong>{rec.resource_type}</strong>
                {rec.chosen?.length ? (
                  rec.chosen.map((c) => (
                    <div key={c.id} className="resource-pick">
                      {c.name} <span className="muted">({c.distance_km} km, {Math.round(c.workload_ratio * 100)}% loaded)</span>
                    </div>
                  ))
                ) : (
                  <div className="gap-text">⚠ {rec.gap}</div>
                )}
              </li>
            ))}
          </ul>
        </div>

        <div className="plan-section">
          <h4>Recommended Hospital</h4>
          {hospital ? (
            <div>
              <strong>{hospital.name}</strong>
              <div className="muted">{hospital.reason}</div>
              {plan.recommended_hospital.alternatives?.length > 0 && (
                <div className="muted" style={{ marginTop: 6 }}>
                  Alternatives: {plan.recommended_hospital.alternatives.map((a) => a.name).join(", ")}
                </div>
              )}
              {plan.recommended_hospital.capacity_caveat && (
                <div className="gap-text" style={{ marginTop: 6 }}>⚠ {plan.recommended_hospital.capacity_caveat}</div>
              )}
            </div>
          ) : (
            <div className="gap-text">⚠ No operational hospital found.</div>
          )}
        </div>

        <div className="plan-section">
          <h4>Risks / Secondary Hazards</h4>
          <ul className="risk-list">
            {plan.risks?.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>

        <div className="plan-section">
          <h4>Response Sequence</h4>
          <ol>
            {plan.actions?.map((a, idx) => (
              <li key={idx}>{a}</li>
            ))}
          </ol>
        </div>
      </div>

      {plan.information_gaps?.length > 0 && (
        <div className="info-gaps">
          <h4>Information Gaps</h4>
          <ul>
            {plan.information_gaps.map((g, idx) => (
              <li key={idx}>{g}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="plan-section" style={{ marginTop: 16 }}>
        <h4>AI Confidence</h4>
        {Object.entries(plan.confidence || {}).map(([k, v]) => (
          <ConfidenceBar key={k} label={k.replace(/_/g, " ")} value={v} />
        ))}
        <p className="muted small">Confidence reflects the AI's certainty in its own analysis, not a guarantee of ground truth.</p>
      </div>

      <details className="explainability-details">
        <summary>Why this recommendation? (AI Explainability)</summary>
        <ul>
          {plan.explainability?.severity_reasons?.map((r, idx) => (
            <li key={idx}>{r}</li>
          ))}
        </ul>
        {plan.knowledge_base_refs?.length > 0 && (
          <p className="muted small">Guidance referenced: {plan.knowledge_base_refs.join(", ")}</p>
        )}
      </details>

      <div className="approval-status-row">
        Approval status: <strong>{plan.approval_status}</strong>
        {plan.approved_by && <span className="muted"> by {plan.approved_by}</span>}
      </div>

      {isPending && (
        <div className="approval-actions">
          <input
            className="text-input"
            value={approverName}
            onChange={(e) => setApproverName(e.target.value)}
            placeholder="Approver name"
          />
          <button className="btn btn-approve" disabled={busy} onClick={() => onApprove(approverName)}>
            APPROVE RESPONSE
          </button>
          <button className="btn btn-reject" disabled={busy} onClick={() => setShowReject((s) => !s)}>
            REJECT
          </button>
          {showReject && (
            <div className="reject-box">
              <input
                className="text-input"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Reason for rejection"
              />
              <button className="btn btn-reject" disabled={busy} onClick={() => onReject(approverName, rejectReason)}>
                Confirm Reject
              </button>
            </div>
          )}
        </div>
      )}

      <p className="safety-note">
        This is an AI-generated recommendation. No real dispatch occurs until an authorized human approves it above; approval here only triggers a simulated dispatch for this demo.
      </p>
    </div>
  );
}
