const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // ignore parse errors
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  listZones: () => request("/api/zones"),
  getZone: (zoneId) => request(`/api/zones/${zoneId}`),
  nearestZone: (lat, lon) => request(`/api/zones/nearest?lat=${lat}&lon=${lon}`),

  subscribe: (phone, zoneId) =>
    request("/api/alerts/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, zone_id: zoneId }),
    }),

  sendAlert: (zoneId, message) =>
    request(`/api/alerts/send/${zoneId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    }),

  submitReport: (formData) =>
    request("/api/reports", { method: "POST", body: formData }),

  listReports: (zoneId) =>
    request(`/api/reports${zoneId ? `?zone_id=${zoneId}` : ""}`),

  updateReportStatus: (reportId, status) => {
    const formData = new FormData();
    formData.append("status", status);
    return request(`/api/reports/${reportId}`, { method: "PATCH", body: formData });
  },

  overview: () => request("/api/admin/overview"),
  actionLog: () => request("/api/admin/actions"),
  addAction: (message, zoneId) =>
    request("/api/admin/actions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, zone_id: zoneId }),
    }),

  simulate: (zoneId, patch) =>
    request(`/api/simulate/${zoneId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    }),

  uploadsUrl: (path) => (path ? `${API_BASE}${path}` : null),
};
