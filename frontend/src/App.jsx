import React, { useEffect, useState } from "react";

import Dashboard from "./pages/Dashboard.jsx";
import Incidents from "./pages/Incidents.jsx";
import IncidentDetail from "./pages/IncidentDetail.jsx";
import Resources from "./pages/Resources.jsx";
import Hospitals from "./pages/Hospitals.jsx";
import MapPage from "./pages/MapPage.jsx";
import Analytics from "./pages/Analytics.jsx";
import Notifications from "./pages/Notifications.jsx";
import AuditLogs from "./pages/AuditLogs.jsx";

import {
  api,
  getStoredUser,
  isAuthenticated,
} from "./api/client.js";


const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "🖥" },
  { id: "incidents", label: "Incidents", icon: "🚨" },
  { id: "map", label: "Resource Map", icon: "🗺" },
  { id: "resources", label: "Resources", icon: "🚑" },
  { id: "hospitals", label: "Hospitals", icon: "🏥" },
  { id: "analytics", label: "Analytics", icon: "📊" },
  { id: "notifications", label: "Notifications", icon: "🔔" },
  { id: "audit", label: "Audit Logs", icon: "📋" },
];


function LoginScreen({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");


  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const result = await api.login(
        email.trim(),
        password
      );

      onLogin(result.user);
    } catch (err) {
      setError(
        err?.message ||
          "Unable to sign in. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  };


  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        background:
          "linear-gradient(135deg, #eef4f8 0%, #f8fafc 100%)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "430px",
          background: "#ffffff",
          borderRadius: "18px",
          padding: "34px",
          boxShadow:
            "0 18px 50px rgba(15, 23, 42, 0.12)",
        }}
      >
        <div
          style={{
            textAlign: "center",
            marginBottom: "28px",
          }}
        >
          <div
            style={{
              fontSize: "52px",
              marginBottom: "10px",
            }}
          >
            🛟
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: "28px",
            }}
          >
            RescueAI
          </h1>

          <p
            style={{
              marginTop: "8px",
              marginBottom: 0,
              color: "#64748b",
              fontSize: "14px",
            }}
          >
            Emergency Response Command Center
          </p>
        </div>


        <form onSubmit={handleSubmit}>
          <div
            style={{
              marginBottom: "18px",
            }}
          >
            <label
              style={{
                display: "block",
                marginBottom: "7px",
                fontWeight: 600,
                fontSize: "14px",
              }}
            >
              Email
            </label>

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              required
              autoComplete="email"
              placeholder="Enter your email"
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "12px 14px",
                border: "1px solid #cbd5e1",
                borderRadius: "10px",
                fontSize: "15px",
                outline: "none",
              }}
            />
          </div>


          <div
            style={{
              marginBottom: "18px",
            }}
          >
            <label
              style={{
                display: "block",
                marginBottom: "7px",
                fontWeight: 600,
                fontSize: "14px",
              }}
            >
              Password
            </label>

            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              required
              autoComplete="current-password"
              placeholder="Enter your password"
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "12px 14px",
                border: "1px solid #cbd5e1",
                borderRadius: "10px",
                fontSize: "15px",
                outline: "none",
              }}
            />
          </div>


          {error && (
            <div
              style={{
                marginBottom: "16px",
                padding: "11px 12px",
                borderRadius: "9px",
                background: "#fef2f2",
                color: "#b91c1c",
                fontSize: "14px",
              }}
            >
              {error}
            </div>
          )}


          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "12px 16px",
              border: "none",
              borderRadius: "10px",
              fontSize: "15px",
              fontWeight: 700,
              cursor: loading
                ? "not-allowed"
                : "pointer",
              background: loading
                ? "#94a3b8"
                : "#0f172a",
              color: "#ffffff",
            }}
          >
            {loading
              ? "Signing in..."
              : "Sign in to Command Center"}
          </button>
        </form>


        <div
          style={{
            marginTop: "22px",
            paddingTop: "18px",
            borderTop: "1px solid #e2e8f0",
            textAlign: "center",
            color: "#64748b",
            fontSize: "12px",
            lineHeight: 1.6,
          }}
        >
          Authorized emergency-response personnel only.
          <br />
          AI recommendations require human approval.
        </div>
      </div>
    </div>
  );
}


export default function App() {
  const [page, setPage] = useState("dashboard");
  const [selectedIncidentId, setSelectedIncidentId] =
    useState(null);

  const [user, setUser] = useState(
    getStoredUser()
  );

  const [authChecking, setAuthChecking] =
    useState(isAuthenticated());


  // ---------------------------------------------------------------------------
  // Validate any previously stored session when the app starts.
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const validateSession = async () => {
      if (!isAuthenticated()) {
        setAuthChecking(false);
        setUser(null);
        return;
      }

      try {
        const currentUser =
          await api.getCurrentUser();

        setUser(currentUser);
      } catch {
        api.logout();
        setUser(null);
      } finally {
        setAuthChecking(false);
      }
    };

    validateSession();
  }, []);


  const openIncident = (id) => {
    setSelectedIncidentId(id);
    setPage("incident-detail");
  };


  const navigate = (id) => {
    setSelectedIncidentId(null);
    setPage(id);
  };


  const handleLogin = (loggedInUser) => {
    setUser(loggedInUser);
    setPage("dashboard");
  };


  const handleLogout = () => {
    api.logout();

    setUser(null);
    setSelectedIncidentId(null);
    setPage("dashboard");
  };


  const renderPage = () => {
    switch (page) {
      case "dashboard":
        return (
          <Dashboard
            onOpenIncident={openIncident}
            onNavigate={navigate}
          />
        );

      case "incidents":
        return (
          <Incidents
            onOpenIncident={openIncident}
          />
        );

      case "incident-detail":
        return (
          <IncidentDetail
            incidentId={selectedIncidentId}
            onBack={() =>
              navigate("incidents")
            }
          />
        );

      case "map":
        return <MapPage />;

      case "resources":
        return <Resources />;

      case "hospitals":
        return <Hospitals />;

      case "analytics":
        return <Analytics />;

      case "notifications":
        return <Notifications />;

      case "audit":
        return <AuditLogs />;

      default:
        return (
          <Dashboard
            onOpenIncident={openIncident}
            onNavigate={navigate}
          />
        );
    }
  };


  // ---------------------------------------------------------------------------
  // Initial authentication check
  // ---------------------------------------------------------------------------

  if (authChecking) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "16px",
          color: "#475569",
        }}
      >
        Checking secure session...
      </div>
    );
  }


  // ---------------------------------------------------------------------------
  // Not logged in -> Command Center login screen
  // ---------------------------------------------------------------------------

  if (!user) {
    return (
      <LoginScreen
        onLogin={handleLogin}
      />
    );
  }


  // ---------------------------------------------------------------------------
  // Authenticated Command Center
  // ---------------------------------------------------------------------------

  return (
    <div className="app-shell">
      <aside className="sidebar">

        <div className="sidebar-brand">
          <span className="brand-icon">
            🛟
          </span>

          <div>
            <div className="brand-title">
              RescueAI
            </div>

            <div className="brand-subtitle">
              Decision-Support Only
            </div>
          </div>
        </div>


        <div
          style={{
            padding: "12px 16px",
            marginBottom: "6px",
            fontSize: "12px",
          }}
        >
          <div
            style={{
              fontWeight: 700,
              marginBottom: "3px",
            }}
          >
            {user.name}
          </div>

          <div
            style={{
              opacity: 0.75,
            }}
          >
            {user.role}
          </div>
        </div>


        <nav>
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${
                page === item.id ||
                (
                  item.id === "incidents" &&
                  page === "incident-detail"
                )
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                navigate(item.id)
              }
            >
              <span className="nav-icon">
                {item.icon}
              </span>{" "}
              {item.label}
            </button>
          ))}
        </nav>


        <div
          style={{
            padding: "14px 16px",
          }}
        >
          <button
            onClick={handleLogout}
            style={{
              width: "100%",
              padding: "9px 12px",
              borderRadius: "8px",
              border:
                "1px solid rgba(255,255,255,0.25)",
              background: "transparent",
              color: "inherit",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Sign Out
          </button>
        </div>


        <div className="sidebar-footer">
          <p>
            Demo/synthetic data only.
            <br />
            AI never dispatches autonomously -
            human approval required for every
            response plan.
          </p>
        </div>

      </aside>

      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  );
}
