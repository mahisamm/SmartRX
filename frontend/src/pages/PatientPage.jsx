import { useEffect, useState } from "react";
import { api, getUser } from "../api.js";
import PrescriptionList from "../components/PrescriptionList.jsx";

export default function PatientPage() {
  const user = getUser();
  const [log, setLog] = useState(null); // null = not loaded yet
  const [loadErr, setLoadErr] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadErr, setUploadErr] = useState("");
  const [lastResult, setLastResult] = useState(null);

  async function loadLog() {
    setLoadErr("");
    try {
      const data = await api.patientLog(user.phone);
      setLog(data);
    } catch (err) {
      // 404 = patient has no record row yet; treat as empty, not an error.
      if (/no records/i.test(err.message)) {
        setLog({ phone: user.phone, name: user.name, prescriptions: [] });
      } else {
        setLoadErr(err.message);
      }
    }
  }

  useEffect(() => {
    loadLog();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function upload(e) {
    e.preventDefault();
    if (!file) return;
    setUploadErr("");
    setLastResult(null);
    setUploading(true);
    try {
      const res = await api.upload(file);
      setLastResult(res);
      setFile(null);
      e.target.reset();
      await loadLog(); // refresh log with the new prescription
    } catch (err) {
      setUploadErr(err.message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="page">
      <section className="card">
        <h2>Upload a prescription</h2>
        <p className="muted">
          Photograph or scan your prescription. We read it automatically — this can take
          5–15 seconds.
        </p>
        <form onSubmit={upload} className="form">
          <input
            type="file"
            accept="image/jpeg,image/png"
            onChange={(e) => setFile(e.target.files[0] || null)}
            disabled={uploading}
          />
          {uploadErr && <p className="error">{uploadErr}</p>}
          <button type="submit" className="primary" disabled={!file || uploading}>
            {uploading ? "Reading prescription…" : "Upload"}
          </button>
        </form>

        {lastResult && (
          <div className="banner ok">
            Added {lastResult.medicines.length} medicine
            {lastResult.medicines.length === 1 ? "" : "s"} from your prescription
            {lastResult.engine ? ` (${lastResult.engine})` : ""}.
          </div>
        )}
      </section>

      <section className="card">
        <h2>Your medicine history</h2>
        {loadErr && <p className="error">{loadErr}</p>}
        {log === null && !loadErr ? (
          <p className="muted">Loading…</p>
        ) : (
          log && <PrescriptionList prescriptions={log.prescriptions} />
        )}
      </section>
    </div>
  );
}
