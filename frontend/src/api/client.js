const BASE = "https://rescueai-39xw.onrender.com/api";

const TOKEN_KEY = "rescueai_access_token";
const USER_KEY = "rescueai_user";


// -----------------------------------------------------------------------------
// Authentication storage helpers
// -----------------------------------------------------------------------------

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const value = localStorage.getItem(USER_KEY);

  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value);
  } catch {
    localStorage.removeItem(USER_KEY);
    return null;
  }
}

export function isAuthenticated() {
  return Boolean(getAccessToken());
}

export function saveSession(accessToken, user) {
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}


// -----------------------------------------------------------------------------
// Main request helper
// -----------------------------------------------------------------------------

async function request(path, options = {}) {
  const token = getAccessToken();

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  // Automatically attach JWT when the user is logged in.
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let detail = res.statusText;

    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // Ignore JSON parsing failure.
    }

    // Remove invalid/expired login automatically.
    if (res.status === 401 && token) {
      clearSession();
    }

    throw new Error(`${res.status}: ${detail}`);
  }

  if (res.status === 204) {
    return null;
  }

  return res.json();
}


// -----------------------------------------------------------------------------
// API
// -----------------------------------------------------------------------------

export const api = {

  // ---------------------------------------------------------------------------
  // Authentication
  // ---------------------------------------------------------------------------

  login: async (email, password) => {
    const data = await request("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
      }),
    });

    if (!data.access_token) {
      throw new Error("Login succeeded but no access token was returned.");
    }

    saveSession(
      data.access_token,
      data.user
    );

    return data;
  },


  getCurrentUser: async () => {
    const user = await request("/auth/me");

    localStorage.setItem(
      USER_KEY,
      JSON.stringify(user)
    );

    return user;
  },


  logout: () => {
    clearSession();
  },


  // ---------------------------------------------------------------------------
  // Incidents
  // ---------------------------------------------------------------------------

  listIncidents: (params = {}) => {
    const qs = new URLSearchParams(params).toString();

    return request(
      `/incidents${qs ? `?${qs}` : ""}`
    );
  },


  getIncident: (id) =>
    request(`/incidents/${id}`),


  // Public emergency-reporting endpoint.
  createIncident: (payload) =>
    request("/incidents", {
      method: "POST",
      body: JSON.stringify(payload),
    }),


  addReport: (id, payload) =>
    request(`/incidents/${id}/reports`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),


  analyzeIncident: (id) =>
    request(`/incidents/${id}/analyze`, {
      method: "POST",
    }),


  getResponsePlan: (id) =>
    request(`/incidents/${id}/response-plan`),


  approveResponse: (id, payload = {}) =>
    request(`/incidents/${id}/approve`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),


  rejectResponse: (id, payload) =>
    request(`/incidents/${id}/reject`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),


  resolveIncident: (id) =>
    request(`/incidents/${id}/resolve`, {
      method: "POST",
    }),


  // ---------------------------------------------------------------------------
  // Resources
  // ---------------------------------------------------------------------------

  listResources: () =>
    request("/resources"),


  listAvailableResources: () =>
    request("/resources/available"),


  // ---------------------------------------------------------------------------
  // Hospitals
  // ---------------------------------------------------------------------------

  listHospitals: () =>
    request("/hospitals"),


  // ---------------------------------------------------------------------------
  // Dashboard
  // ---------------------------------------------------------------------------

  dashboardStats: () =>
    request("/dashboard/stats"),


  dashboardAnalytics: () =>
    request("/dashboard/analytics"),


  // ---------------------------------------------------------------------------
  // Audit logs
  // ---------------------------------------------------------------------------

  listAuditLogs: (incidentId) =>
    request(
      `/audit-logs${
        incidentId
          ? `?incident_id=${encodeURIComponent(incidentId)}`
          : ""
      }`
    ),


  // ---------------------------------------------------------------------------
  // Notifications
  // ---------------------------------------------------------------------------

  listNotifications: () =>
    request("/notifications"),


  // ---------------------------------------------------------------------------
  // Demo mode
  // ---------------------------------------------------------------------------

  loadDemoScenario: () =>
    request("/demo/load-scenario", {
      method: "POST",
    }),
};
