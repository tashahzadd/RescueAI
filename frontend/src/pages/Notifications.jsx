import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";

export default function Notifications() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listNotifications().then(setNotes).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-header"><h2>Notifications</h2></div>
      {loading && <p className="muted">Loading notifications...</p>}
      <div className="section-card">
        {notes.length === 0 && !loading && <p className="muted">No notifications yet.</p>}
        <ul className="notification-list">
          {notes.map((n) => (
            <li key={n.id}>
              <span className="notif-badge">{n.is_simulated ? "SIMULATED" : "LIVE"}</span>
              {n.message}
              <span className="muted small"> - {new Date(n.created_at).toLocaleString()}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
