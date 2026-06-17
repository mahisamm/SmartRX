# smartRX — Project Report

**Course:** Capstone Project
**Team:** 2 members
**Duration:** 1 week
**Date:** June 2026

---

## 1. Problem

Patients accumulate paper prescriptions across visits, clinics, and doctors. When they
see a new doctor, that history is missing, illegible, or forgotten. Doctors then
prescribe without a reliable view of what the patient is already taking — risking drug
interactions, duplicate therapy, and wasted consult time.

## 2. Solution

smartRX digitizes the prescription at the point of care:

1. A **patient** photographs a prescription in the app.
2. **AI extracts** the structured medicine data (name, dose, frequency, duration, notes).
3. A **doctor** enters the patient's phone number and instantly sees the full medicine
   history plus an **AI-generated summary**.

Phone number is the patient's identity — no app install friction for the patient's
existing records to be found.

## 3. Scope (what we built in one week)

In scope (the core loop, end to end):
- Patient + doctor registration / login with hashed passwords and JWT sessions.
- Image upload with validation (type, size).
- Two-engine OCR/AI extraction pipeline with structured, validated output.
- Patient medicine history view.
- Doctor lookup + AI summary view.
- Stub mode so the app runs without paid API keys (for development/demo).

Deliberately out of scope — see [§8 Future Work](#8-future-work).

## 4. Architecture

```
React (Vite) SPA  ──HTTP/JSON──>  FastAPI  ──>  SQLAlchemy  ──>  SQLite
  /patient  /doctor                  │
                                     ├─> OCR pipeline (Tesseract + Gemini vision)
                                     └─> Gemini (summary generation)
```

- **Frontend (Lane B):** React 18 + Vite + react-router. Thin `fetch` client, token in
  localStorage, role-based routing.
- **Backend (Lane A):** FastAPI + SQLAlchemy 2.0 (typed models), Pydantic v2 schemas.
- **Contract-first:** the two lanes were built in parallel against a frozen JSON
  contract ([API_CONTRACT.md](API_CONTRACT.md)), so neither side blocked the other.
- **DB:** SQLite for zero-setup dev; swappable to Postgres via `DATABASE_URL`.

### Data model
```
users (phone PK) 1───many prescriptions 1───many medicines
```
Doctors and patients are both `users`, separated by `role`.

## 5. The OCR / AI pipeline (key design decision)

We use **two engines together**, not one:

| Engine | Role |
|--------|------|
| Tesseract | Local OCR; gives a **mean word-confidence** signal for printed text. |
| Gemini vision | Primary structured extractor; reads handwriting Tesseract can't. |

**Fallback rule:** if Tesseract's confidence is below a threshold
(`TESSERACT_CONF_FLOOR`, default 60 — i.e. likely handwritten), we trust Gemini vision
and label the result `gemini_vision`; otherwise `tesseract+gemini`. This gives a
defensible "two-engine grading" story and a confidence number for the UI.

A **separate** Gemini call turns the stored medicine log into the doctor's summary —
extraction and summarization are distinct concerns with distinct prompts.

**Safety:** all model output passes through a Pydantic schema (`ExtractionResult`)
before it can touch the database, so malformed or hallucinated JSON is rejected at the
boundary.

## 6. Security

- Passwords are **bcrypt-hashed** (passlib), never stored in plaintext.
- **JWT bearer** auth protects upload, patient log, and summary endpoints.
- **Role enforcement:** only patients upload; only doctors fetch summaries.
- **Input validation:** image MIME type and 10 MB size cap on upload.

**Known limitation (accepted for v1):** any authenticated user can look up any phone
number — there is no per-record consent/access model. This is documented and the demo
uses synthetic data only. A consent model is the first item in Future Work.

## 7. Testing & demo

- `seed.py` populates demo users + prescriptions (including an empty-history patient to
  show the empty state). Demo doctor `9000000001`, patients `9876543210` /
  `9123456780` / `9555500000`, password `demo1234`.
- Stub mode lets the full loop be demoed without API cost or network.
- FastAPI's `/docs` (Swagger UI) provides an interactive endpoint test surface.

## 8. Future Work

- **Access control / consent** so a doctor only sees patients who shared with them.
- **Compliance:** encryption at rest, audit logging, ephemeral image storage (HIPAA-grade).
- **Production AI:** prompt hardening, retries/timeouts, cost controls; replace stub path.
- **Postgres + Alembic** migrations (currently `create_all` on boot).
- **Clinical value-add:** drug-interaction / allergy warnings, reminders, refills.
- **Reach:** mobile-native capture, multi-language OCR, doctor e-signature.
- **Engineering:** automated test suite + CI, rate limiting, observability.

## 9. Team & timeline

Two developers, one week, two parallel lanes against a fixed API contract:

| Day | Focus |
|-----|-------|
| 1 | Contract + backend scaffold + React scaffold (stub mode end-to-end) |
| 2 | Upload wired end to end |
| 3 | Real Gemini vision + summary integration |
| 4 | Doctor lookup + summary view |
| 5 | Auth, polish, error/empty states |
| 6 | Demo seed data + this report |
| 7 | Buffer / bug-fix |
