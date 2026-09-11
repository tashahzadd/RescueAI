import React from "react";

export default function StatCard({ label, value, accent }) {
  return (
    <div className="stat-card" style={accent ? { borderLeft: `4px solid ${accent}` } : undefined}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
