import React from "react";

const COLORS = {
  CRITICAL: "#dc2626",
  HIGH: "#ea580c",
  MEDIUM: "#ca8a04",
  LOW: "#16a34a",
};

export default function SeverityBadge({ severity }) {
  if (!severity) return <span className="badge badge-muted">UNASSESSED</span>;
  const color = COLORS[severity] || "#64748b";
  return (
    <span className="badge" style={{ backgroundColor: `${color}22`, color, border: `1px solid ${color}55` }}>
      {severity}
    </span>
  );
}
