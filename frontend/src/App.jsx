import { Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";
import { getUser, clearSession } from "./api.js";
import LoginPage from "./pages/LoginPage.jsx";
import PatientPage from "./pages/PatientPage.jsx";
import DoctorPage from "./pages/DoctorPage.jsx";

function Protected({ role, children }) {
  const user = getUser();
  if (!user) return <Navigate to="/" replace />;
  if (role && user.role !== role) return <Navigate to="/" replace />;
  return children;
}

function Header() {
  const user = getUser();
  const navigate = useNavigate();
  if (!user) return null;
  return (
    <header className="topbar">
      <Link to={user.role === "doctor" ? "/doctor" : "/patient"} className="brand">
        smartRX
      </Link>
      <div className="topbar-right">
        <span className="who">{user.name} · {user.role}</span>
        <button
          className="link-btn"
          onClick={() => { clearSession(); navigate("/"); }}
        >
          Log out
        </button>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="app">
      <Header />
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route
          path="/patient"
          element={
            <Protected role="patient">
              <PatientPage />
            </Protected>
          }
        />
        <Route
          path="/doctor"
          element={
            <Protected role="doctor">
              <DoctorPage />
            </Protected>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
