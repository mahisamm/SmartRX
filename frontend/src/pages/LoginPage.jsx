import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api, setSession, getUser } from "../api.js";

const EMPTY = { phone: "", password: "", name: "", role: "patient", hospital_name: "", specialization: "" };

export default function LoginPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState(EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const existing = getUser();
    if (existing) {
      navigate(existing.role === "doctor" ? "/doctor" : "/patient", { replace: true });
    }
  }, [navigate]);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res =
        mode === "register"
          ? await api.register({
              phone: form.phone,
              password: form.password,
              name: form.name,
              role: form.role,
              hospital_name: form.role === "doctor" && form.hospital_name ? form.hospital_name : undefined,
              specialization: form.role === "doctor" && form.specialization ? form.specialization : undefined,
            })
          : await api.login(form.phone, form.password);
      setSession(res.token, res.user);
      navigate(res.user.role === "doctor" ? "/doctor" : "/patient", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card auth-card">
      <h1>smartRX</h1>
      <p className="muted">Prescription tracking, made simple.</p>

      <div className="tabs">
        <button className={mode === "login" ? "tab active" : "tab"} onClick={() => { setMode("login"); setError(""); }}>
          Log in
        </button>
        <button className={mode === "register" ? "tab active" : "tab"} onClick={() => { setMode("register"); setError(""); }}>
          Register
        </button>
      </div>

      <form onSubmit={submit} className="form">
        <label>
          Phone
          <input type="tel" value={form.phone} onChange={(e) => update("phone", e.target.value)} required autoComplete="username" />
        </label>

        {mode === "register" && (
          <label>
            Name
            <input type="text" value={form.name} onChange={(e) => update("name", e.target.value)} required />
          </label>
        )}

        <label>
          Password
          <input
            type="password"
            value={form.password}
            onChange={(e) => update("password", e.target.value)}
            required
            autoComplete={mode === "register" ? "new-password" : "current-password"}
          />
        </label>

        {mode === "register" && (
          <label>
            Role
            <select value={form.role} onChange={(e) => update("role", e.target.value)}>
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
            </select>
          </label>
        )}

        {mode === "register" && form.role === "doctor" && (
          <>
            <label>
              Hospital / Clinic Name
              <input
                type="text"
                value={form.hospital_name}
                onChange={(e) => update("hospital_name", e.target.value)}
                placeholder="e.g. City Medical Centre"
              />
            </label>
            <label>
              Specialization
              <input
                type="text"
                value={form.specialization}
                onChange={(e) => update("specialization", e.target.value)}
                placeholder="e.g. General Medicine"
              />
            </label>
          </>
        )}

        {error && <p className="error">{error}</p>}

        <button type="submit" className="primary" disabled={busy}>
          {busy ? "Working…" : mode === "register" ? "Create account" : "Log in"}
        </button>
      </form>
    </div>
  );
}
