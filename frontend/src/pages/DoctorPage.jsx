import { useState } from "react";
import { api } from "../api.js";
import PrescriptionList from "../components/PrescriptionList.jsx";

export default function DoctorPage() {
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [log, setLog] = useState(null);
  const [summary, setSummary] = useState(null);

  async function lookup(e) {
    e.preventDefault();
    if (!phone.trim()) return;
    setError("");
    setLog(null);
    setSummary(null);
    setBusy(true);
    try {
      // Log first (fast), then summary (slow — Gemini).
      const logData = await api.patientLog(phone.trim());
      setLog(logData);
      const summaryData = await api.summary(phone.trim());
      setSummary(summaryData);
    } catch (err) {
      if (/no records/i.test(err.message)) {
        setError("No patient found for that phone number.");
      } else {
        setError(err.message);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <section className="card">
        <h2>Look up a patient</h2>
        <p className="muted">Enter a patient phone number to see their history and an AI summary.</p>
        <form onSubmit={lookup} className="form row">
          <input
            type="tel"
            placeholder="Phone number"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            disabled={busy}
          />
          <button type="submit" className="primary" disabled={busy || !phone.trim()}>
            {busy ? <><span className="spinner" />Looking up…</> : "Look up"}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
      </section>

      {log && (
        <section className="card">
          <h2>{log.name}</h2>
          <span className="muted">{log.phone}</span>

          <div className="summary-block">
            <h3>AI summary</h3>
            {summary === null ? (
              <p className="muted">Generating summary…</p>
            ) : summary.medicine_count === 0 ? (
              <p className="muted">No medicines on record — nothing to summarize yet.</p>
            ) : (
              <p>{summary.summary}</p>
            )}
          </div>

          <h3>Prescription history</h3>
          <PrescriptionList prescriptions={log.prescriptions} />
        </section>
      )}
    </div>
  );
}
