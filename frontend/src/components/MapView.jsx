import React, { useMemo } from "react";

const TYPE_COLORS = {
  incident: "#dc2626",
  Ambulance: "#2563eb",
  "Rescue Team": "#16a34a",
  "Search & Rescue Team": "#16a34a",
  "Fire Unit": "#ea580c",
  "Medical Team": "#7c3aed",
  "Heavy Rescue Equipment": "#0891b2",
  "Water Tanker": "#0ea5e9",
  Shelter: "#a16207",
  "Utility Team": "#64748b",
  "Food Supply": "#84cc16",
  hospital: "#db2777",
};

const WIDTH = 640;
const HEIGHT = 440;
const PADDING = 30;

/**
 * A dependency-free SVG map. Plots synthetic lat/lon coordinates onto a flat
 * projection - sufficient for a city-scale hackathon demo without requiring
 * an internet-connected tile provider. NOT a substitute for a real GIS.
 */
export default function MapView({ incidents = [], resources = [], hospitals = [] }) {
  const points = useMemo(() => {
    const all = [
      ...incidents.map((i) => ({ lat: i.latitude, lon: i.longitude })),
      ...resources.map((r) => ({ lat: r.latitude, lon: r.longitude })),
      ...hospitals.map((h) => ({ lat: h.latitude, lon: h.longitude })),
    ].filter((p) => typeof p.lat === "number" && typeof p.lon === "number");

    if (all.length === 0) {
      return { minLat: 24.8, maxLat: 24.95, minLon: 66.95, maxLon: 67.1 };
    }
    const lats = all.map((p) => p.lat);
    const lons = all.map((p) => p.lon);
    const pad = 0.01;
    return {
      minLat: Math.min(...lats) - pad,
      maxLat: Math.max(...lats) + pad,
      minLon: Math.min(...lons) - pad,
      maxLon: Math.max(...lons) + pad,
    };
  }, [incidents, resources, hospitals]);

  const project = (lat, lon) => {
    const { minLat, maxLat, minLon, maxLon } = points;
    const x = PADDING + ((lon - minLon) / (maxLon - minLon || 1)) * (WIDTH - 2 * PADDING);
    const y = HEIGHT - PADDING - ((lat - minLat) / (maxLat - minLat || 1)) * (HEIGHT - 2 * PADDING);
    return [x, y];
  };

  return (
    <div className="map-wrapper">
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="map-svg" role="img" aria-label="Incident and resource map">
        <rect x="0" y="0" width={WIDTH} height={HEIGHT} fill="#0b1220" rx="8" />
        {Array.from({ length: 6 }).map((_, i) => (
          <line key={`h${i}`} x1={0} y1={(HEIGHT / 6) * i} x2={WIDTH} y2={(HEIGHT / 6) * i} stroke="#1e293b" strokeWidth="1" />
        ))}
        {Array.from({ length: 8 }).map((_, i) => (
          <line key={`v${i}`} x1={(WIDTH / 8) * i} y1={0} x2={(WIDTH / 8) * i} y2={HEIGHT} stroke="#1e293b" strokeWidth="1" />
        ))}

        {hospitals.map((h) => {
          const [x, y] = project(h.latitude, h.longitude);
          return (
            <g key={`hosp-${h.id}`}>
              <rect x={x - 6} y={y - 6} width="12" height="12" fill={TYPE_COLORS.hospital} rx="2" />
              <title>{`${h.name} (Hospital) - ${h.emergency_beds} ER beds, ${h.icu_beds} ICU`}</title>
            </g>
          );
        })}

        {resources.map((r) => {
          const [x, y] = project(r.latitude, r.longitude);
          const color = TYPE_COLORS[r.resource_type] || "#94a3b8";
          const dispatched = r.status === "DISPATCHED";
          return (
            <g key={`res-${r.id}`}>
              <circle cx={x} cy={y} r={5} fill={color} opacity={dispatched ? 0.4 : 1} stroke={dispatched ? "#fff" : "none"} strokeDasharray={dispatched ? "2,2" : undefined} />
              <title>{`${r.name} (${r.resource_type}) - ${r.status}`}</title>
            </g>
          );
        })}

        {incidents.map((inc) => {
          const [x, y] = project(inc.latitude, inc.longitude);
          return (
            <g key={`inc-${inc.id}`}>
              <circle cx={x} cy={y} r={9} fill="none" stroke={TYPE_COLORS.incident} strokeWidth="2" />
              <circle cx={x} cy={y} r={4} fill={TYPE_COLORS.incident} />
              <title>{`${inc.incident_type} - ${inc.severity || "unassessed"} - ${inc.location}`}</title>
            </g>
          );
        })}
      </svg>
      <div className="map-legend">
        <span><i className="dot" style={{ background: TYPE_COLORS.incident, borderRadius: "50%" }} /> Incident</span>
        <span><i className="dot" style={{ background: TYPE_COLORS.hospital }} /> Hospital</span>
        <span><i className="dot" style={{ background: TYPE_COLORS.Ambulance, borderRadius: "50%" }} /> Ambulance</span>
        <span><i className="dot" style={{ background: TYPE_COLORS["Rescue Team"], borderRadius: "50%" }} /> Rescue/SAR</span>
        <span><i className="dot" style={{ background: TYPE_COLORS["Fire Unit"], borderRadius: "50%" }} /> Fire Unit</span>
      </div>
      <p className="map-disclaimer">Synthetic demo coordinates (Karachi sample environment) - not real emergency resource locations.</p>
    </div>
  );
}
