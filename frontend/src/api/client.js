const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
export const WS_URL = API_URL.replace(/^http/, "ws");

let authToken = localStorage.getItem("ai_crm_token") || "";

export function setAuthToken(token) {
  authToken = token || "";
  if (authToken) {
    localStorage.setItem("ai_crm_token", authToken);
  } else {
    localStorage.removeItem("ai_crm_token");
  }
}

async function request(path, options = {}) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    ...(options.headers ?? {}),
  };
  const response = await fetch(`${API_URL}${path}`, {
    headers,
    ...options,
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.detail || `Request failed with status ${response.status}`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return data;
}

export const api = {
  login: (payload) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  register: (payload) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  me: () => request("/auth/me"),
  health: () => request("/health"),
  listLeads: (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        params.set(key, value);
      }
    });
    const query = params.toString();
    return request(`/leads${query ? `?${query}` : ""}`);
  },
  createLead: (payload) =>
    request("/leads", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateLead: (id, payload) =>
    request(`/leads/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteLead: (id) =>
    request(`/leads/${id}`, {
      method: "DELETE",
    }),
  enrichLead: (leadId, context = {}) =>
    request("/webhooks/lead-enrichment", {
      method: "POST",
      body: JSON.stringify({ lead_id: leadId, context }),
    }),
  scoreLead: (leadId, context = {}) =>
    request("/webhooks/lead-score", {
      method: "POST",
      body: JSON.stringify({ lead_id: leadId, context }),
    }),
  listTasks: () => request("/tasks"),
  createTask: (payload) =>
    request("/webhooks/create-task", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateTask: (id, payload) =>
    request(`/tasks/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  listEmails: () => request("/emails"),
  generateEmail: (payload) =>
    request("/emails/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  analytics: () => request("/analytics/overview"),
  importLeads: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return request("/leads/import", {
      method: "POST",
      body: formData,
    });
  },
  sendReport: () =>
    request("/reports/send-summary", {
      method: "POST",
    }),
};
