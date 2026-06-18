# smartRX — Developer Reference

## What this app does

smartRX is a prescription-tracking system for patients and doctors.

- **Patients** upload prescription images (photos/scans). AI (Gemini Vision + Tesseract OCR) extracts medicines, doctor name, hospital, date. Patient reviews extracted data in a verification modal before it is saved.
- **Doctors** look up any patient by phone number and get an AI-generated structured clinical summary: current medicines, inferred conditions, allergies, drug interactions, health trend, consultation timeline. Doctors can add consultation notes per patient.
- Both roles have settings (language, notification preferences, doctor credentials). All doctor accesses to patient data are logged in an audit trail visible to the patient.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.111, Python 3.11+ |
| ORM | SQLAlchemy 2.0 (mapped_column / Mapped style) |
| DB | SQLite (dev) — swap `DATABASE_URL` env var for Postgres |
| Auth | JWT via python-jose; bcrypt password hashing |
| AI extraction | Gemini Vision API (google-genai SDK) + Tesseract OCR fallback |
| AI summary | Gemini text (gemini-2.5-flash by default) — structured JSON output |
| Frontend | React 18 + Vite |
| Routing | react-router-dom v6 |
| i18n | Custom localStorage-backed module (`frontend/src/i18n.js`) |
| Notifications | Web Notifications API (browser-native) |

---

## Project Layout

```
smartRX/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, router mounting
│   │   ├── config.py            # Settings from env vars / .env
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models.py            # ORM models (see DB Schema below)
│   │   ├── schemas.py           # Pydantic v2 request/response shapes
│   │   ├── auth.py              # JWT creation + require_role dependency
│   │   ├── gemini_client.py     # Gemini vision_extract + generate_structured_summary
│   │   └── routers/
│   │       ├── auth_router.py          # POST /auth/register, POST /auth/login
│   │       ├── prescriptions_router.py # POST /upload, GET /patient/{phone}, PATCH/DELETE /prescription/{id}
│   │       ├── summary_router.py       # GET /summary/{phone}
│   │       ├── notes_router.py         # POST/GET /patient/{phone}/notes
│   │       ├── settings_router.py      # GET/PATCH /settings
│   │       └── audit_router.py         # GET /audit-log
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx              # Router: / → /patient | /doctor
    │   ├── api.js               # All fetch calls (thin client, no state)
    │   ├── i18n.js              # English + Hindi translations, t() helper
    │   ├── styles.css           # All styles (single file, ~1200 lines)
    │   └── pages/
    │       ├── LoginPage.jsx    # Login + Register (patient/doctor)
    │       ├── PatientPage.jsx  # Patient dashboard
    │       └── DoctorPage.jsx   # Doctor dashboard
    └── vite.config.js
```

---

## Running Locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# runs on http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# runs on http://localhost:5173
```

**Environment variables** (backend/.env):
```
GEMINI_API_KEY=your_key_here        # omit → stub mode (canned data, no real AI)
DATABASE_URL=sqlite:///./smartrx.db # default SQLite
JWT_SECRET=change-me-in-prod
GEMINI_MODEL=gemini-2.5-flash       # default model
```

Stub mode: without `GEMINI_API_KEY`, Gemini calls return canned data. App fully bootable and testable without a key.

---

## Database Schema

```
users (phone PK, name, role, password_hash, created_at)
  └─── prescriptions (id, patient_phone FK, doctor_name, hospital, date,
  │                   image_path, engine, confidence, created_at)
  │         └─── medicines (id, prescription_id FK, name, dose, frequency,
  │                         duration, instructions)
  │
  └─── access_logs (id, accessed_by_phone, accessed_by_name, patient_phone FK,
  │                 action, accessed_at)
  │         action values: "view_log" | "view_summary"
  │
  └─── doctor_notes (id, doctor_phone FK, patient_phone FK, note, created_at)
  │         NOTE: no SQLAlchemy relationship() on this model — two FKs to users
  │         would cause AmbiguousForeignKeysError. Use explicit db.get() lookups.
  │
  └─── user_settings (phone PK FK users, language, notifications_enabled,
                      reminder_time, hospital_name, specialization)
                      Auto-created on first GET /settings or on doctor register.
```

---

## API Routes (v2.0.0)

| Method | Path | Auth | Who | Description |
|--------|------|------|-----|-------------|
| POST | `/auth/register` | none | any | Register patient or doctor. Doctor fields: hospital_name, specialization (optional). |
| POST | `/auth/login` | none | any | Returns JWT token + user object. |
| POST | `/upload` | JWT | patient | Upload prescription image. Returns PrescriptionOut with extracted data + confidence. |
| PATCH | `/prescription/{id}` | JWT | patient (own) | Edit extracted prescription fields (doctor/hospital/date/medicines). |
| DELETE | `/prescription/{id}` | JWT | patient (own) | Delete prescription + removes image file from disk. |
| GET | `/patient/{phone}` | JWT | doctor | Get patient's full prescription log. Writes AccessLog entry. |
| GET | `/summary/{phone}` | JWT | doctor | Get structured AI summary with drug interactions. Writes AccessLog entry. |
| POST | `/patient/{phone}/notes` | JWT | doctor | Add consultation note for patient. |
| GET | `/patient/{phone}/notes` | JWT | doctor or own-patient | Read notes for patient. |
| GET | `/settings` | JWT | any | Get current user's settings. Auto-creates defaults if absent. |
| PATCH | `/settings` | JWT | any | Update any/all settings fields. |
| GET | `/audit-log` | JWT | any | Patients see who accessed their data. Doctors see their own access history. |

---

## AI Pipeline

### Prescription Extraction (on upload)
1. File saved to `./uploads/`
2. Tesseract OCR runs on image → confidence score
3. If Tesseract confidence < 60 (configurable), Gemini Vision used instead
4. `vision_extract()` → returns `{ doctor_name, hospital, date, confidence, medicines[] }`
5. Validated by `ExtractionResult` Pydantic schema
6. Saved to DB as Prescription + Medicine rows
7. Frontend shows **ExtractionVerifyModal** — patient reviews, edits, then confirms (PATCH) or discards (DELETE)

### Structured Summary + Drug Interaction Detection (on doctor request)
1. All patient prescriptions fetched from DB
2. `generate_structured_summary(name, prescriptions)` called
3. Gemini receives full prescription history as JSON + structured prompt
4. Returns JSON with 7 keys:
   - `clinical_notes` — 2-3 sentence doctor-facing overview
   - `current_medicines[]` — deduplicated, with status (ongoing/completed/unknown)
   - `conditions[]` — inferred conditions with status (stable/improving/worsening)
   - `allergies[]` — only if explicitly mentioned in prescriptions
   - `last_consultation` — date of most recent prescription
   - `trend` — stable/improving/worsening/insufficient_data
5. Parsed by `_parse_structured()` into typed Pydantic models
6. Returned as `SummaryOut.structured`

---

## Authentication & Authorization

- JWT stored in `localStorage` as `smartrx_token`
- User object stored as `smartrx_user` (phone, name, role)
- `require_role("doctor")` / `require_role("patient")` FastAPI dependencies enforce access
- Patients can only access/modify their own prescriptions
- Doctors can read any patient's data but cannot modify prescriptions
- Every doctor access to patient data creates an `AccessLog` row

---

## Frontend Architecture

### State management
No global state library. Each page manages its own state via `useState` / `useEffect`.

### PatientPage panels (nav tabs)
1. **Upload** — dropzone → ExtractionVerifyModal → history refresh
2. **History** — list of saved prescriptions
3. **Notifications** — Web Notifications API permission + dose reminder settings
4. **Audit** — table showing which doctors accessed patient's data
5. **Settings** — language toggle (EN/HI), notification prefs, persisted to backend

### DoctorPage panels
1. **Search** — lookup patient by phone, loads log + summary + notes in parallel
2. **Sidebar** — avatar, hospital badge, recent patients (session memory only)
3. **PatientPanel** — 3 tabs: Summary | History | Notes
   - Summary tab: clinical overview, trend badge, medicines grid, conditions, allergies
   - History tab: prescription timeline
   - Notes tab: add note, view all notes sorted newest-first
4. **Doctor Settings** — hospital/specialization fields

### i18n
- `frontend/src/i18n.js` — ~60 key translations in English + Hindi
- `getLang()` / `setLang(lang)` backed by localStorage
- `t(key)` returns string for current language
- Language preference also synced to backend via `PATCH /settings`

---

## Known Architectural Notes

- `DoctorNote` has two FKs to `users` table. No SQLAlchemy `relationship()` declared on it — would cause `AmbiguousForeignKeysError`. All note queries use explicit `db.get(User, phone)` lookups.
- `UserSettings` auto-created on first access. On doctor register, settings row is seeded with hospital_name/specialization via `db.flush()` after the user insert.
- Gemini stub mode is transparent — same code path, returns `_STUB_EXTRACTION` / `_STUB_STRUCTURED` canned dicts.
- Upload directory defaults to `./uploads` (relative to where uvicorn runs, i.e. `backend/uploads/`). StaticFiles mounted at `/uploads`.
- SQLite default: no connection pooling tuning needed for dev. For Postgres in prod, set `DATABASE_URL` env var — SQLAlchemy URL format handles the rest.

---

## What Could Be Added Next

### High value (feature gaps vs competitors like Practo/PharmEasy)
1. **Drug Interaction Detection** — See the full implementation guide below. Was built, then removed; ready to re-add.
2. **Medication reminders** — current notification system asks permission but reminders are `setInterval`-based (tab-active only). Replace with Service Worker push for true background notifications.
3. **Medicine refill reminders** — based on `duration` field in prescriptions, calculate expected run-out date and alert patient.
4. **Doctor search by specialization** — patients currently know doctor's phone; no discovery mechanism.
5. **Prescription sharing** — patient shares read-only link to prescription summary with a new doctor.
6. **Multi-language OCR** — Tesseract supports many languages; Hindi prescription text not currently handled.

---

## Future Feature: Drug Interaction Detection

> **Status:** Was fully implemented and working, then removed from the codebase. All architectural context preserved here so it can be re-added cleanly.

### What it does
When a doctor views a patient's summary, Gemini analyzes the patient's entire prescription history and flags known drug-drug interactions. Each interaction has:
- Which medicines are involved
- Severity: `mild` / `moderate` / `severe`
- Clinical description of the interaction

### Design decisions made previously
- Detection is **on-demand** — runs when doctor calls `GET /summary/{phone}`, not in the background
- Patient does **not** see interaction warnings (doctor-only in v1)
- Gemini reasons from prescription text only, no external drug database
- No longitudinal tracking — each summary call is stateless

### Better design for v2 (suggested improvements)
- Also run interaction check after patient confirms extraction in `ExtractionVerifyModal`, so patient sees warning before doctor does
- Add a `POST /check-interactions` endpoint patients can call independently
- Fire a browser notification to patient if severe interaction detected on upload

---

### Step-by-step implementation guide

#### 1. Add `DrugInteraction` schema — `backend/app/schemas.py`

Add after `StructuredCondition`:

```python
class DrugInteraction(BaseModel):
    medicines: list[str]
    severity: str  # "mild" | "moderate" | "severe"
    description: str
```

Add `interactions` field to `StructuredSummary`:

```python
class StructuredSummary(BaseModel):
    clinical_notes: str
    current_medicines: list[StructuredMed] = []
    conditions: list[StructuredCondition] = []
    allergies: list[str] = []
    interactions: list[DrugInteraction] = []   # <-- add this line
    last_consultation: Optional[str] = None
    trend: str = "insufficient_data"
```

#### 2. Update Gemini prompt — `backend/app/gemini_client.py`

Add `interactions` to the JSON shape in `_STRUCTURED_SUMMARY_PROMPT`:

```
  "interactions": [
    {{ "medicines": ["med1", "med2"], "severity": "mild|moderate|severe", "description": "brief clinical note" }}
  ],
```

Add to the Rules section:
```
- Flag drug interactions you are confident about. Leave interactions [] if none detected.
```

Add `"interactions": []` to the stub dict `_STUB_STRUCTURED` and to the fallback return in `generate_structured_summary`.

#### 3. Parse interactions in summary router — `backend/app/routers/summary_router.py`

Update import:
```python
from ..schemas import (
    SummaryOut, StructuredSummary, StructuredMed, StructuredCondition, DrugInteraction,
)
```

Add parsing block inside `_parse_structured()`, before the `return StructuredSummary(...)`:

```python
interactions = []
for ix in raw.get("interactions") or []:
    if isinstance(ix, dict):
        interactions.append(DrugInteraction(
            medicines=ix.get("medicines") or [],
            severity=ix.get("severity", "mild"),
            description=ix.get("description", ""),
        ))
```

Add `interactions=interactions` to the `StructuredSummary(...)` constructor call.

#### 4. Display in DoctorPage — `frontend/src/pages/DoctorPage.jsx`

**In `PatientPanel`:** Add interaction warning badge to the header stats:

```jsx
const hasInteractions = summary?.structured?.interactions?.length > 0;

// Inside patient-header-stats:
{hasInteractions && (
  <div className="stat-pill stat-pill-warn">
    <span className="stat-num">⚠</span>
    <span className="stat-label">Interactions</span>
  </div>
)}
```

**In `SummaryTab`:** Add block at top of returned JSX, before Clinical Notes:

```jsx
{s?.interactions?.length > 0 && (
  <div className="interactions-alert-block">
    <div className="interactions-alert-title">
      ⚠ Drug Interaction{s.interactions.length > 1 ? "s" : ""} Detected
    </div>
    {s.interactions.map((ix, i) => (
      <div key={i} className={`interaction-item severity-${ix.severity}`}>
        <div className="interaction-meds">{ix.medicines.join(" + ")}</div>
        <div className="interaction-severity-badge severity-badge-${ix.severity}">{ix.severity}</div>
        <p className="interaction-desc">{ix.description}</p>
      </div>
    ))}
  </div>
)}
```

#### 5. Add CSS — `frontend/src/styles.css`

Add this block (insert before `/* ── Conditions ── */`):

```css
/* ── Drug Interactions ── */
.interactions-alert-block {
  background: #fff5f5;
  border: 2px solid #fca5a5;
  border-radius: var(--radius);
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.interactions-alert-title {
  font-weight: 800;
  font-size: 0.97rem;
  color: #991b1b;
}

.interaction-item {
  background: var(--card);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 8px;
}

.interaction-meds {
  font-weight: 700;
  font-size: 0.93rem;
  flex: 1;
  min-width: 140px;
}

.interaction-severity-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  flex-shrink: 0;
}

.severity-mild     .interaction-severity-badge,
.severity-badge-mild     { background: #fef9c3; color: #854d0e; }
.severity-moderate .interaction-severity-badge,
.severity-badge-moderate { background: #fed7aa; color: #9a3412; }
.severity-severe   .interaction-severity-badge,
.severity-badge-severe   { background: #fee2e2; color: #991b1b; }

.interaction-desc {
  margin: 4px 0 0;
  font-size: 0.88rem;
  color: var(--muted);
  width: 100%;
}
```

#### 6. Verify
```bash
# Backend
cd backend
python -c "from app.schemas import DrugInteraction, StructuredSummary; print('OK')"
python -c "from app.main import app; print([r.path for r in app.routes])"

# Frontend
cd frontend
npm run build
```

No DB migration needed — interactions are not stored, generated fresh on every summary call.
