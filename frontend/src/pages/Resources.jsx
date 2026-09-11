import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";

export default function Resources() {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("ALL");

  useEffect(() => {
    api.listResources().then(setResources).finally(() => setLoading(false));
  }, []);

  const filtered = filter === "ALL" ? resources : resources.filter((r) => r.status === filter);

  return (
    <div>
      <div className="page-header">
        <h2>Resources</h2>
        <select className="select-input" value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="ALL">All statuses</option>
          <option value="AVAILABLE">Available</option>
          <option value="DISPATCHED">Dispatched</option>
          <option value="ON_SCENE">On scene</option>
          <option value="OUT_OF_SERVICE">Out of service</option>
        </select>
      </div>
      {loading && <p className="muted">Loading resources...</p>}
      <div className="section-card">
        <table className="data-table">
          <thead>
            <tr><th>Name</th><th>Type</th><th>Status</th><th>Capacity</th><th>Workload</th><th>Organization</th></tr>
          </thead>
          <tbody>
            {filtered.map((r) => (
              <tr key={r.id}>
                <td>{r.name}</td>
                <td>{r.resource_type}</td>
                <td><span className={`status-tag status-${r.status.toLowerCase()}`}>{r.status}</span></td>
                <td>{r.capacity}</td>
                <td>{r.current_workload}</td>
                <td>{r.organization}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
