import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";
import MapView from "../components/MapView.jsx";

export default function MapPage() {
  const [incidents, setIncidents] = useState([]);
  const [resources, setResources] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.listIncidents(), api.listResources(), api.listHospitals()])
      .then(([i, r, h]) => {
        setIncidents(i);
        setResources(r);
        setHospitals(h);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-header"><h2>Resource Map</h2></div>
      {loading && <p className="muted">Loading map...</p>}
      <div className="section-card">
        <MapView incidents={incidents} resources={resources} hospitals={hospitals} />
      </div>
    </div>
  );
}
