# smartRX

AI-powered prescription management + patient health tracking.

**Core loop:** a patient photographs a prescription → AI extracts structured medicine
data → a doctor enters the patient's phone number → sees the medicine history plus an
AI-generated summary.

College capstone, 2-person team, 1-week MVP. Scope is deliberately tight — see
[Future Work](#future-work) for everything intentionally left out.

---

## Stack

| Layer    | Tech |
|----------|------|
| Frontend | React 18 + Vite + react-router-dom |
| Backend  | Python FastAPI + SQLAlchemy 2.0 |
| Database | SQLite (dev) — swap to Postgres via `DATABASE_URL` |
| OCR / AI | Tesseract (cross-check) + Gemini vision (extraction) + Gemini (summary) |
| Auth     | JWT (python-jose), bcrypt password hashing (passlib) |

The frontend and backend talk over the fixed JSON contract in
[API_CONTRACT.md](API_CONTRACT.md). Build either side against that file.

### How the OCR/AI pipeline works
1. Image goes to **Tesseract** for a printed-text confidence signal.
2. Image also goes to **Gemini vision**, which returns structured medicines.
3. If Tesseract's mean word confidence is below `TESSERACT_CONF_FLOOR` (default 60),
   the prescription is likely handwritten → we trust Gemini vision and label the
   engine `gemini_vision`; otherwise `tesseract+gemini`.
4. A **separate Gemini call** turns the stored medicine log into a doctor-facing summary.

All AI output is validated by Pydantic (`ExtractionResult`) before it touches the DB.

### Stub mode
With no `GEMINI_API_KEY` set, the backend runs in **stub mode**: Gemini calls return
canned data so the whole app boots and round-trips end to end without an API key.
Set the key (and the real `google-genai` wiring, Day 3) to go live.

---

## Run it

Two terminals. Backend first.

### 1. Backend (port 8000)
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
uvicorn app.main:app --reload
```
API docs: http://localhost:8000/docs · health: http://localhost:8000/health

> Tesseract is optional for dev. If the `tesseract` binary isn't installed, the
> backend skips the confidence cross-check and relies on Gemini. Install it later
> for the two-engine grading story (Windows: UB-Mannheim build; macOS: `brew install
> tesseract`; Debian/Ubuntu: `apt install tesseract-ocr`).

### 2. Frontend (port 5173)
```bash
cd frontend
npm install
cp .env.example .env          # Windows: copy .env.example .env
npm run dev
```
Open http://localhost:5173.

### Demo data (optional but recommended)
Seed sample users + prescriptions (incl. an empty-history patient for the empty state):
```bash
cd backend
python seed.py
```
Logins (all password `demo1234`): doctor `9000000001`; patients `9876543210`,
`9123456780`, `9555500000`.

### Try the loop
1. Register a **patient** → upload any JPEG/PNG → see the (stubbed) extracted medicine
   appear in the history.
2. Register a **doctor** (log out first) → enter the patient's phone → see the history
   and AI summary.

See [REPORT.md](REPORT.md) for the full capstone write-up.

---

## Project layout
```
smartRX/
├── API_CONTRACT.md        # the frozen FE↔BE JSON contract
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app, CORS, router mounts, /health
│   │   ├── config.py      # settings (env-driven)
│   │   ├── database.py    # engine + session + get_db
│   │   ├── models.py      # User, Prescription, Medicine
│   │   ├── schemas.py     # Pydantic I/O + LLM-output validation
│   │   ├── auth.py        # hashing, JWT, role guards
│   │   ├── gemini_client.py  # shared Gemini wrapper (stubbed)
│   │   ├── ocr.py         # Tesseract + Gemini extraction
│   │   └── routers/       # auth, prescriptions, summary
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── api.js         # thin fetch client (matches the contract)
    │   ├── App.jsx        # routes + role guard
    │   ├── pages/         # Login, Patient, Doctor
    │   └── components/    # PrescriptionList
    └── .env.example
```

---

## Security notes (v1)
- Passwords are bcrypt-hashed, never stored in plaintext.
- JWT bearer auth gates `/upload`, `/patient/{phone}`, `/summary/{phone}`.
- **Known limitation:** any authenticated user can look up *any* phone number — there
  is no per-record access control. Accepted for the v1 demo; see Future Work. Do not
  put real patient data in this build.
- Uploaded images are stored on local disk under `UPLOAD_DIR`; no encryption at rest.

## Future Work
Intentionally out of scope for the 1-week MVP:
- Access control / consent model so a doctor only sees patients who shared with them.
- HIPAA-grade handling: encryption at rest, audit logs, ephemeral image storage.
- Real `google-genai` wiring (replace stub mode), prompt hardening, retries.
- Postgres + Alembic migrations (currently `create_all` on boot, SQLite).
- Medication interaction / allergy warnings, reminders, refills.
- Mobile-native capture, multi-language OCR, doctor e-sign.
- Tests + CI, rate limiting, observability.
