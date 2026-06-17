// Thin API client. Matches API_CONTRACT.md. Token kept in localStorage for the demo.
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export function getToken() {
  return localStorage.getItem("smartrx_token");
}
export function setSession(token, user) {
  localStorage.setItem("smartrx_token", token);
  localStorage.setItem("smartrx_user", JSON.stringify(user));
}
export function getUser() {
  const raw = localStorage.getItem("smartrx_user");
  return raw ? JSON.parse(raw) : null;
}
export function clearSession() {
  localStorage.removeItem("smartrx_token");
  localStorage.removeItem("smartrx_user");
}

async function handle(res) {
  if (!res.ok) {
    let detail = `request failed (${res.status})`;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

function authHeaders() {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export const api = {
  register: (body) =>
    fetch(`${BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(handle),

  login: (phone, password) =>
    fetch(`${BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, password }),
    }).then(handle),

  upload: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetch(`${BASE}/upload`, {
      method: "POST",
      headers: { ...authHeaders() },
      body: fd,
    }).then(handle);
  },

  patientLog: (phone) =>
    fetch(`${BASE}/patient/${encodeURIComponent(phone)}`, {
      headers: { ...authHeaders() },
    }).then(handle),

  summary: (phone) =>
    fetch(`${BASE}/summary/${encodeURIComponent(phone)}`, {
      headers: { ...authHeaders() },
    }).then(handle),
};
