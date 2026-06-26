import { lazy, Suspense, Component } from "react";
import { useNavigate } from "react-router-dom";

// Code-split the 3D brain: content paints instantly, three.js streams in.
const BrainBackground = lazy(() => import("../components/BrainBackground.jsx"));

/**
 * The 3D brain is decorative. If three.js, the GLB load, or a shader throws,
 * this boundary swallows it so the page content can never be blanked by it.
 */
class BrainBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { dead: false };
  }
  static getDerivedStateFromError() {
    return { dead: true };
  }
  componentDidCatch(err) {
    // decorative layer — log, don't crash the page
    console.warn("BrainBackground failed, hiding it:", err);
  }
  render() {
    return this.state.dead ? null : this.props.children;
  }
}

/* ---- inline line icons (stroke = currentColor) ---- */
const Icon = {
  pill: (
    <>
      <path d="M10.6 20.4 3.6 13.4a4.95 4.95 0 0 1 7-7l7 7a4.95 4.95 0 0 1-7 7z" />
      <path d="M7 10 14 17" />
    </>
  ),
  camera: (
    <>
      <path d="M3 7h3l1.5-2h9L18 7h3a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1z" />
      <circle cx="12" cy="13" r="3.5" />
    </>
  ),
  pulse: <path d="M2 12h3.5l2.5 7 4-15 2.5 8H20" />,
  alert: (
    <>
      <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
      <path d="M12 9v4M12 17h.01" />
    </>
  ),
  shield: (
    <>
      <path d="M12 3l7 3v5c0 4.5-3 7.3-7 9-4-1.7-7-4.5-7-9V6l7-3z" />
      <path d="M9.2 11.8 11 13.6 14.8 9.8" />
    </>
  ),
  brain: (
    <>
      <path d="M9.5 3A2.5 2.5 0 0 0 7 5.5 2.5 2.5 0 0 0 4.5 8 2.5 2.5 0 0 0 5 13a2.5 2.5 0 0 0 2 4 2.5 2.5 0 0 0 5 .5V3.5A2.5 2.5 0 0 0 9.5 3z" />
      <path d="M14.5 3A2.5 2.5 0 0 1 17 5.5 2.5 2.5 0 0 1 19.5 8 2.5 2.5 0 0 1 19 13a2.5 2.5 0 0 1-2 4 2.5 2.5 0 0 1-5 .5" />
    </>
  ),
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
};

function Glyph({ name }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {Icon[name]}
    </svg>
  );
}

const CAPABILITIES = [
  {
    icon: "camera",
    title: "Reads any prescription",
    body: "Snap a photo or scan. Gemini Vision and OCR pull out every medicine, dose, the doctor, hospital and date — even from messy handwriting.",
  },
  {
    icon: "pulse",
    title: "Builds a clinical picture",
    body: "The brain reasons across your whole history to produce a doctor-ready summary: current medicines, inferred conditions, allergies and health trend.",
  },
  {
    icon: "alert",
    title: "Flags hidden risks",
    body: "It cross-checks medicines for drug interactions and surfaces severity-graded warnings before they reach the patient.",
  },
  {
    icon: "shield",
    title: "Keeps you in control",
    body: "Every time a doctor opens your records it is written to an audit trail only you can see. Private by design, transparent by default.",
  },
];

const STEPS = [
  { n: "01", title: "Snap", body: "A patient uploads a prescription photo from any phone." },
  { n: "02", title: "Understand", body: "The AI extracts the details and the patient verifies them in seconds." },
  { n: "03", title: "Share", body: "A doctor looks up the patient and gets an instant, structured clinical summary." },
];

export default function AboutPage() {
  const navigate = useNavigate();

  return (
    <div className="about-screen">
      <BrainBoundary>
        <Suspense fallback={null}>
          <BrainBackground />
        </Suspense>
      </BrainBoundary>
      <div className="about-veil" aria-hidden="true" />

      {/* top nav */}
      <nav className="about-nav">
        <button type="button" className="about-brand" onClick={() => navigate("/")}>
          <span className="about-brand-mark"><Glyph name="pill" /></span>
          <span className="about-brand-name">smartRX</span>
        </button>
        <div className="about-nav-right">
          <button type="button" className="about-nav-link" onClick={() => navigate("/")}>
            Log in
          </button>
          <button type="button" className="about-nav-cta" onClick={() => navigate("/")}>
            Get started <Glyph name="arrow" />
          </button>
        </div>
      </nav>

      <main className="about-main">
        {/* hero */}
        <section className="about-hero">
          <span className="about-eyebrow">
            <span className="about-eyebrow-dot" /> The AI behind your care
          </span>
          <h1 className="about-hero-title">
            A medical brain that <span className="about-accent">reads, remembers</span> and reasons.
          </h1>
          <p className="about-hero-sub">
            smartRX turns a pile of prescription photos into living medical memory. Patients
            scan what their doctors prescribe; our AI extracts it, tracks it over time, and hands
            any treating doctor a clear clinical picture in seconds — so care decisions are made
            with the full story, not a fragment of it.
          </p>
          <div className="about-hero-actions">
            <button type="button" className="about-primary" onClick={() => navigate("/")}>
              Get started <Glyph name="arrow" />
            </button>
            <button type="button" className="about-ghost" onClick={() => navigate("/")}>
              Back to login
            </button>
          </div>
        </section>

        {/* capabilities */}
        <section className="about-section">
          <h2 className="about-section-title">
            <span className="about-section-ico"><Glyph name="brain" /></span>
            What the brain does
          </h2>
          <div className="about-cards">
            {CAPABILITIES.map((c) => (
              <article className="about-card" key={c.title}>
                <span className="about-card-ico"><Glyph name={c.icon} /></span>
                <h3>{c.title}</h3>
                <p>{c.body}</p>
              </article>
            ))}
          </div>
        </section>

        {/* how it works */}
        <section className="about-section">
          <h2 className="about-section-title">How it works</h2>
          <div className="about-steps">
            {STEPS.map((s) => (
              <div className="about-step" key={s.n}>
                <span className="about-step-n">{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* closing CTA */}
        <section className="about-cta-band">
          <h2>Bring your prescriptions to life.</h2>
          <p>Join smartRX and let the medical brain do the remembering.</p>
          <button type="button" className="about-primary" onClick={() => navigate("/")}>
            Create your account <Glyph name="arrow" />
          </button>
        </section>

        <footer className="about-foot">
          smartRX · Smarter medical AI, brighter human life.
        </footer>
      </main>
    </div>
  );
}
