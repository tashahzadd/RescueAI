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
              marginBottom: "4px",
              color: "#475569",
              fontSize: "14px",
              fontWeight: 600,
            }}
          >
            AI Emergency Response System
          </p>

          <p
            style={{
              marginTop: "4px",
              marginBottom: 0,
              color: "#64748b",
              fontSize: "13px",
            }}
          >
            Pak Angels GenAI & Agentic AI — Cohort 11
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
          Team RescueAI — Cohort 11 Hackathon Project
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


  if (!user) {
    return (
      <LoginScreen
        onLogin={handleLogin}
      />
    );
  }


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
              AI Emergency Response System
            </div>
          </div>

        </div>


        <div
          style={{
            padding: "10px 16px 14px",
            marginBottom: "4px",
            borderBottom:
              "1px solid rgba(255,255,255,0.10)",
          }}
        >
          <div
            style={{
              fontSize: "12px",
              fontWeight: 700,
              marginBottom: "4px",
            }}
          >
            Pak Angels — Cohort 11
          </div>

          <div
            style={{
              fontSize: "11px",
              opacity: 0.72,
              lineHeight: 1.5,
            }}
          >
            GenAI & Agentic AI Hackathon
            <br />
            Team RescueAI
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
            marginTop: "auto",
          }}
        >
          <div
            style={{
              marginBottom: "10px",
              fontSize: "11px",
              opacity: 0.75,
              lineHeight: 1.45,
            }}
          >
            Signed in as
            <br />

            <strong
              style={{
                fontSize: "12px",
              }}
            >
              {user.name}
            </strong>
          </div>


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
            Cohort 11 Hackathon Project
            <br />
            Human-in-the-loop AI Emergency Response
            <br />
            Demo / synthetic operational data
          </p>
        </div>

      </aside>


      <main className="main-content">
        {renderPage()}
      </main>

    </div>
  );
}
