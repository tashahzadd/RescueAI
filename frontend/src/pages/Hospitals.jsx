import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";

const TRUST_COLORS = { OFFICIAL: "#16a34a", LIVE: "#2563eb", REPORTED: "#ca8a04", PUBLIC: "#0891b2", DEMO: "#64748b" };

export default function Hospitals() {
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listHospitals().then(setHospitals).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-header"><h2>Hospitals</h2></div>
      {loading && <p className="muted">Loading hospitals...</p>}
      <p className="muted small" style={{ marginTop: -8, marginBottom: 16 }}>
        Bed/ICU figures below are <strong>reported capacity</strong>, not confirmed live availability, unless a hospital's trust level is <strong>LIVE</strong>. See backend/data/SOURCES.md for provenance details.
      </p>
      <div className="hospital-grid">
        {hospitals.map((h) => {
          const total = h.emergency_beds + h.icu_beds;
          const loadPct = total ? Math.round((h.current_load / total) * 100) : 0;
          const trustColor = TRUST_COLORS[h.trust_level] || "#64748b";
          return (
            <div className="hospital-card" key={h.id}>
              <div className="hospital-card-header">
                <h4>{h.name}</h4>
                <span className={`status-tag status-${h.status.toLowerCase()}`}>{h.status}</span>
              </div>
              <div className="muted small">
                {h.district ? `${h.district} - ` : ""}{h.facility_type || ""}
              </div>
              <div className="hospital-stats">
                <div><span className="muted">Emergency beds</span><div>{h.emergency_beds}</div></div>
                <div><span className="muted">ICU beds</span><div>{h.icu_beds}</div></div>
                <div><span className="muted">Trauma capacity</span><div>{h.trauma_capacity}</div></div>
              </div>
              <div className="confidence-track" style={{ marginTop: 10 }}>
                <div
                  className="confidence-fill"
                  style={{ width: `${loadPct}%`, backgroundColor: loadPct > 80 ? "#dc2626" : loadPct > 50 ? "#ca8a04" : "#16a34a" }}
                />
              </div>
              <div className="muted small">{loadPct}% current load (reported)</div>
              <div style={{ marginTop: 10 }}>
                <span className="badge" style={{ backgroundColor: `${trustColor}22`, color: trustColor, border: `1px solid ${trustColor}55` }}>
                  {h.trust_level || "DEMO"}
                </span>
                {h.source_name && <div className="muted small" style={{ marginTop: 4 }}>Source: {h.source_name}</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
