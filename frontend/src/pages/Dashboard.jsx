import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import SeverityBadge from "../components/SeverityBadge";

function MetricCard({
  icon,
  label,
  value,
  subtitle,
  className = "",
}) {
  return (
    <div className={`dashboard-metric-card ${className}`}>
      <div className="dashboard-metric-icon">{icon}</div>

      <div className="dashboard-metric-content">
        <div className="dashboard-metric-label">{label}</div>

        <div className="dashboard-metric-value">
          {value}
        </div>

        {subtitle && (
          <div className="dashboard-metric-subtitle">
            {subtitle}
          </div>
        )}
      </div>
    </div>
  );
}

function ResourceCard({
  icon,
  title,
  value,
  status,
  className = "",
}) {
  return (
    <div className={`resource-summary-card ${className}`}>
      <div className="resource-summary-icon">
        {icon}
      </div>

      <div className="resource-summary-title">
        {title}
      </div>

      <div className="resource-summary-value">
        {value}
      </div>

      <div className="resource-summary-status">
        {status}
      </div>
    </div>
  );
}

export default function Dashboard({
  onOpenIncident,
  onNavigate,
}) {
  const [stats, setStats] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [hospitals, setHospitals] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");

        const [
          statsData,
          incidentsData,
          hospitalsData,
        ] = await Promise.all([
          api.dashboardStats(),
          api.listIncidents(),
          api.listHospitals(),
        ]);

        if (cancelled) return;

        setStats(statsData || {});

        setIncidents(
          Array.isArray(incidentsData)
            ? incidentsData
            : incidentsData?.items || []
        );

        setHospitals(
          Array.isArray(hospitalsData)
            ? hospitalsData
            : hospitalsData?.items || []
        );
      } catch (err) {
        console.error("Dashboard load failed:", err);

        if (!cancelled) {
          setError(
            err?.message ||
              "Unable to load dashboard information."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  const activeIncidents =
    stats?.active_incidents ?? 0;

  const criticalIncidents =
    stats?.critical_incidents ?? 0;

  const resolvedIncidents =
    stats?.resolved_incidents ?? 0;

  const pendingPlans =
    stats?.pending_approvals ?? 0;

  const ambulances =
    stats?.ambulances_available ?? 0;

  const rescueTeams =
    stats?.rescue_teams_available ?? 0;

  const fireUnits =
    stats?.fire_units_available ?? 0;

  const totalAvailableResources =
    ambulances +
    rescueTeams +
    fireUnits;

  const totalIncidents = useMemo(() => {
    if (incidents.length > 0) {
      return incidents.length;
    }

    return activeIncidents + resolvedIncidents;
  }, [
    incidents,
    activeIncidents,
    resolvedIncidents,
  ]);

  const highCount = useMemo(() => {
    return incidents.filter(
      (incident) =>
        String(
          incident?.severity || ""
        ).toUpperCase() === "HIGH"
    ).length;
  }, [incidents]);

  const recentIncidents = useMemo(() => {
    return [...incidents]
      .sort((a, b) => {
        const dateA = new Date(
          a?.created_at ||
            a?.updated_at ||
            0
        );

        const dateB = new Date(
          b?.created_at ||
            b?.updated_at ||
            0
        );

        return dateB - dateA;
      })
      .slice(0, 6);
  }, [incidents]);

  if (!stats && loading) {
    return (
      <div className="modern-dashboard">
        <div className="dashboard-loading">
          Loading RescueAI Command Center...
        </div>
      </div>
    );
  }

  return (
    <div className="modern-dashboard">
      {/* HEADER */}

      <div className="dashboard-top-header">
        <div>
          <h1 className="dashboard-welcome-title">
            RescueAI Command Center
          </h1>

          <p className="dashboard-welcome-subtitle">
            AI-assisted emergency response and
            resource coordination across Pakistan
          </p>
        </div>

        <div className="dashboard-header-actions">
          <div className="system-live-badge">
            <span className="live-dot" />
            System Operational
          </div>

          <button
            className="dashboard-demo-button"
            onClick={() =>
              onNavigate?.("incidents")
            }
          >
            View Incidents
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {/* PRIMARY METRICS */}

      <div className="dashboard-metric-grid">
        <MetricCard
          icon="🚨"
          label="Critical Incidents"
          value={criticalIncidents}
          subtitle="Require immediate attention"
          className="metric-critical"
        />

        <MetricCard
          icon="⚠️"
          label="Active Incidents"
          value={activeIncidents}
          subtitle="Currently being monitored"
          className="metric-active"
        />

        <MetricCard
          icon="📋"
          label="Total Incidents"
          value={totalIncidents}
          subtitle="Recorded in the system"
          className="metric-total"
        />

        <MetricCard
          icon="🚑"
          label="Available Resources"
          value={totalAvailableResources}
          subtitle="Ambulances, rescue and fire units"
          className="metric-resources"
        />

        <MetricCard
          icon="🏥"
          label="Hospitals in Network"
          value={hospitals.length}
          subtitle="Emergency care facilities"
          className="metric-hospitals"
        />

        <MetricCard
          icon="🤖"
          label="Pending AI Plans"
          value={pendingPlans}
          subtitle="Awaiting human approval"
          className="metric-ai"
        />
      </div>

      {/* SECONDARY STATS */}

      <div className="dashboard-secondary-stats">
        <div className="secondary-stat">
          <span className="secondary-stat-icon">
            🔥
          </span>

          <div>
            <span className="secondary-stat-value">
              {highCount}
            </span>

            <span className="secondary-stat-label">
              High Priority
            </span>
          </div>
        </div>

        <div className="secondary-stat">
          <span className="secondary-stat-icon">
            ✅
          </span>

          <div>
            <span className="secondary-stat-value">
              {resolvedIncidents}
            </span>

            <span className="secondary-stat-label">
              Resolved Incidents
            </span>
          </div>
        </div>

        <div className="secondary-stat">
          <span className="secondary-stat-icon">
            🚒
          </span>

          <div>
            <span className="secondary-stat-value">
              {fireUnits}
            </span>

            <span className="secondary-stat-label">
              Fire Units Available
            </span>
          </div>
        </div>

        <div className="secondary-stat">
          <span className="secondary-stat-icon">
            🧑‍🚒
          </span>

          <div>
            <span className="secondary-stat-value">
              {rescueTeams}
            </span>

            <span className="secondary-stat-label">
              Rescue Teams Available
            </span>
          </div>
        </div>
      </div>

      {/* MAIN GRID */}

      <div className="dashboard-main-grid">
        <div className="dashboard-panel">
          <div className="dashboard-panel-header">
            <div>
              <h3>Operational Overview</h3>

              <p>
                Live emergency and response
                readiness summary
              </p>
            </div>

            <button
              className="panel-action-link"
              onClick={() =>
                onNavigate?.("map")
              }
            >
              View Map
            </button>
          </div>

          <div className="operational-overview">
            <div className="overview-main-number">
              {activeIncidents}
            </div>

            <div className="overview-main-label">
              Active Incidents
            </div>

            <div className="overview-status-grid">
              <div className="overview-status-item">
                <span className="status-dot critical-dot" />
                <strong>{criticalIncidents}</strong>
                Critical
              </div>

              <div className="overview-status-item">
                <span className="status-dot high-dot" />
                <strong>{highCount}</strong>
                High
              </div>

              <div className="overview-status-item">
                <span className="status-dot resolved-dot" />
                <strong>{resolvedIncidents}</strong>
                Resolved
              </div>

              <div className="overview-status-item">
                <span className="status-dot resource-dot" />
                <strong>
                  {totalAvailableResources}
                </strong>
                Resources
              </div>
            </div>

            <button
              className="overview-map-button"
              onClick={() =>
                onNavigate?.("map")
              }
            >
              Open Operational Map
            </button>
          </div>
        </div>

        {/* RECENT INCIDENTS */}

        <div className="dashboard-panel">
          <div className="dashboard-panel-header">
            <div>
              <h3>Recent Incidents</h3>

              <p>
                Latest emergency reports
              </p>
            </div>

            <button
              className="panel-action-link"
              onClick={() =>
                onNavigate?.("incidents")
              }
            >
              View All
            </button>
          </div>

          <div className="recent-incident-list">
            {recentIncidents.length === 0 ? (
              <div className="empty-dashboard-state">
                No recent incidents available.
              </div>
            ) : (
              recentIncidents.map(
                (incident) => (
                  <button
                    key={incident.id}
                    className="recent-incident-item"
                    onClick={() =>
                      onOpenIncident?.(
                        incident.id
                      )
                    }
                  >
                    <div className="recent-incident-icon">
                      🚨
                    </div>

                    <div className="recent-incident-main">
                      <div className="recent-incident-title">
                        {incident.title ||
                          incident.incident_type ||
                          "Emergency Incident"}
                      </div>

                      <div className="recent-incident-location">
                        📍{" "}
                        {incident.location_text ||
                          incident.location ||
                          "Location unavailable"}
                      </div>
                    </div>

                    <div className="recent-incident-badge">
                      <SeverityBadge
                        severity={
                          incident.severity ||
                          "UNKNOWN"
                        }
                      />
                    </div>
                  </button>
                )
              )
            )}
          </div>
        </div>
      </div>

      {/* BOTTOM GRID */}

      <div className="dashboard-bottom-grid">
        <div className="dashboard-panel">
          <div className="dashboard-panel-header">
            <div>
              <h3>Resource Status</h3>

              <p>
                Current emergency-response
                capacity
              </p>
            </div>

            <button
              className="panel-action-link"
              onClick={() =>
                onNavigate?.("resources")
              }
            >
              Manage Resources
            </button>
          </div>

          <div className="resource-summary-grid">
            <ResourceCard
              icon="🚑"
              title="Ambulances"
              value={ambulances}
              status="Available"
              className="resource-ambulance"
            />

            <ResourceCard
              icon="🧑‍🚒"
              title="Rescue Teams"
              value={rescueTeams}
              status="Available"
              className="resource-rescue"
            />

            <ResourceCard
              icon="🚒"
              title="Fire Units"
              value={fireUnits}
              status="Available"
              className="resource-fire"
            />

            <ResourceCard
              icon="🏥"
              title="Hospitals"
              value={hospitals.length}
              status="In Network"
              className="resource-hospital"
            />
          </div>
        </div>

        {/* SYSTEM STATUS */}

        <div className="dashboard-panel">
          <div className="dashboard-panel-header">
            <div>
              <h3>System Status</h3>

              <p>
                RescueAI service availability
              </p>
            </div>
          </div>

          <div className="system-status-list">
            {[
              "AI Decision Support",
              "Incident Management",
              "Resource Coordination",
              "Hospital Network",
              "Human Approval Layer",
            ].map((item, index) => (
              <div
                className="system-status-row"
                key={item}
              >
                <span>
                  <span className="system-green-dot" />
                  {item}
                </span>

                <span className="system-online">
                  {index === 4
                    ? "ACTIVE"
                    : "ONLINE"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* SAFETY BANNER */}

      <div className="dashboard-safety-banner">
        <div>
          <span className="dashboard-info-icon">
            i
          </span>

          RescueAI provides AI-assisted
          recommendations. Operational deployment
          decisions remain subject to authorized
          human review and approval.
        </div>

        <div className="dashboard-team-label">
          Team RescueAI • Pak Angels Cohort 11
        </div>
      </div>
    </div>
  );
}
