import React from "react";

export default function ConfidenceBar({ label, value }) {
  const pct = Math.round((value || 0) * 100);
  const color = pct >= 80 ? "#16a34a" : pct >= 55 ? "#ca8a04" : "#dc2626";
  return (
    <div className="confidence-row">
      <div className="confidence-label">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="confidence-track">
        <div className="confidence-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}
