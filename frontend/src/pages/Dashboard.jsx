import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";
import SeverityBadge from "../components/SeverityBadge.jsx";


function MetricCard({
  icon,
  label,
  value,
  className = "",
  subtitle,
}) {
  return (
    <div className={`dashboard-metric-card ${className}`}>
      <div className="dashboard-metric-icon">
        {icon}
      </div>

      <div className="dashboard-metric-content">
        <div className="dashboard-metric-label">
          {label}
        </div>

        <div className="dashboard-metric-value">
          {value ?? 0}
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
        {value ?? 0}
      </div>

      <div className="resource-summary-status">
        Available
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
  const [demoLoading, setDemoLoading] =
    useState(false);

  const [error, setError] = useState(null);


  const load = async () => {
    setLoading(true);
    setError(null);

    try {
      const [
        dashboardStats,
        incidentData,
        hospitalData,
      ] = await Promise.all([
        api.dashboardStats(),
        api.listIncidents(),
        api.listHospitals(),
      ]);

      setStats(dashboardStats);
      setIncidents(incidentData);
      setHospitals(hospitalData);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    load();
  }, []);


  const runDemo = async () => {
    setDemoLoading(true);
    setError(null);

    try {
      const res =
        await api.loadDemoScenario();

      await load();

      onOpenIncident(
        res.incident_id
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setDemoLoading(false);
    }
  };


  const recentIncidents =
    useMemo(
      () => incidents.slice(0, 6),
      [incidents]
    );


  const totalAvailableResources =
    (stats?.ambulances_available || 0) +
    (stats?.rescue_teams_available || 0) +
    (stats?.fire_units_available || 0);


  const activeCount =
    stats?.active_incidents || 0;

  const criticalCount =
    stats?.critical_incidents || 0;

  const highCount =
    stats?.high_incidents || 0;

  const resolvedCount =
    stats?.resolved_incidents || 0;


  return (
    <div className="modern-dashboard">

      {/* ---------------------------------------------------------
          TOP HEADER
      --------------------------------------------------------- */}

      <div className="dashboard-top-header">

        <div>
          <h1 className="dashboard-welcome-title">
            Welcome back, RescueAI Team
          </h1>

          <p className="dashboard-welcome-subtitle">
            Here&apos;s the current emergency-response
            situation across the system.
          </p>
        </div>


        <div className="dashboard-header-actions">

          <div className="system-live-badge">
            <span className="live-dot"></span>
            Live System
          </div>


          <button
            className="dashboard-demo-button"
            onClick={runDemo}
            disabled={demoLoading}
          >
            {demoLoading
              ? "Loading..."
              : "▶ Load Demo Incident"}
          </button>

        </div>
      </div>


      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}


      {loading && (
        <div className="dashboard-loading">
          Loading RescueAI operational data...
        </div>
      )}


      {stats && (
        <>

          {/* -----------------------------------------------------
              KPI CARDS
          ----------------------------------------------------- */}

          <div className="dashboard-metric-grid">

            <MetricCard
              icon="🚨"
              label="Critical Incidents"
              value={criticalCount}
              className="metric-critical"
              subtitle="Highest response priority"
            />


            <MetricCard
              icon="⚠️"
              label="Active Incidents"
              value={activeCount}
              className="metric-active"
              subtitle="Currently under response"
            />


            <MetricCard
              icon="📋"
              label="Total Incidents"
              value={incidents.length}
              className="metric-total"
              subtitle="Recorded in RescueAI"
            />


            <MetricCard
              icon="🚑"
              label="Available Resources"
              value={totalAvailableResources}
              className="metric-resources"
              subtitle="Ready for assignment"
            />


            <MetricCard
              icon="🏥"
              label="Hospitals in Network"
              value={hospitals.length}
              className="metric-hospitals"
              subtitle="Registered facilities"
            />


            <MetricCard
              icon="🤖"
              label="Pending AI Plans"
              value={stats.pending_approvals}
              className="metric-ai"
              subtitle="Awaiting human approval"
            />

          </div>


          {/* -----------------------------------------------------
              SECONDARY KPI ROW
          ----------------------------------------------------- */}

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
                  {resolvedCount}
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
                  {stats.fire_units_available}
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
                  {stats.rescue_teams_available}
                </span>

                <span className="secondary-stat-label">
                  Rescue Teams Available
                </span>
              </div>
            </div>

          </div>


          {/* -----------------------------------------------------
              MAIN DASHBOARD AREA
          ----------------------------------------------------- */}

          <div className="dashboard-main-grid">

            {/* Operational Overview */}

            <div class
