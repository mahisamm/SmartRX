// Renders the medicine log shared by patient + doctor views.
// `prescriptions` is the PrescriptionLite[] shape from API_CONTRACT.md.
export default function PrescriptionList({ prescriptions }) {
  if (!prescriptions || prescriptions.length === 0) {
    return <p className="muted">No prescriptions on record yet.</p>;
  }
  return (
    <div className="rx-list">
      {prescriptions.map((rx) => (
        <article key={rx.id} className="rx-card">
          <div className="rx-head">
            <strong>{rx.doctor_name || "Unknown doctor"}</strong>
            <span className="muted">{rx.date || "no date"}</span>
          </div>
          {rx.hospital && <div className="muted small">{rx.hospital}</div>}
          <table className="med-table">
            <thead>
              <tr>
                <th>Medicine</th>
                <th>Dose</th>
                <th>Frequency</th>
                <th>Duration</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {rx.medicines.map((m, i) => (
                <tr key={i}>
                  <td>{m.name}</td>
                  <td>{m.dose || "—"}</td>
                  <td>{m.frequency || "—"}</td>
                  <td>{m.duration || "—"}</td>
                  <td>{m.instructions || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      ))}
    </div>
  );
}
