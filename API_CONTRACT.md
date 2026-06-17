# smartRX API Contract

The fixed boundary between **Lane A (backend, FastAPI)** and **Lane B (frontend, React)**.
Build against this. Change it only by editing this file and telling the other person.

Base URL (dev): `http://localhost:8000`
All bodies are JSON. Auth via `Authorization: Bearer <token>` header after login.

---

## Auth

### POST /auth/register
Register a patient or doctor.
```json
// request
{ "phone": "9876543210", "name": "Asha Rao", "password": "secret", "role": "patient" }
// role: "patient" | "doctor"

// 201 response
{ "token": "<jwt>", "user": { "phone": "9876543210", "name": "Asha Rao", "role": "patient" } }

// 409 if phone already registered
{ "detail": "phone already registered" }
```

### POST /auth/login
```json
// request
{ "phone": "9876543210", "password": "secret" }

// 200 response
{ "token": "<jwt>", "user": { "phone": "9876543210", "name": "Asha Rao", "role": "patient" } }

// 401 on wrong password / unknown phone
{ "detail": "invalid phone or password" }
```

---

## Prescriptions (patient)

### POST /upload
Multipart form upload of a prescription image. Auth required (patient).
- form field: `file` (image/jpeg, image/png), max 10MB
```json
// 201 response — the extracted, structured prescription
{
  "id": 12,
  "phone": "9876543210",
  "doctor_name": "Dr. Mehta",
  "hospital": "City Clinic",
  "date": "2026-06-15",
  "engine": "gemini_vision",          // "gemini_vision" | "tesseract+gemini"
  "confidence": 0.87,
  "medicines": [
    { "name": "Amoxicillin", "dose": "500mg", "frequency": "1-0-1", "duration": "5 days", "instructions": "after food" }
  ]
}

// 400 bad file (not an image / too large / unreadable by both engines)
{ "detail": "could not read prescription image" }
```

### GET /patient/{phone}
Medicine log for a phone. Auth required.
```json
// 200 response
{
  "phone": "9876543210",
  "name": "Asha Rao",
  "prescriptions": [
    {
      "id": 12, "doctor_name": "Dr. Mehta", "hospital": "City Clinic", "date": "2026-06-15",
      "medicines": [ { "name": "Amoxicillin", "dose": "500mg", "frequency": "1-0-1", "duration": "5 days", "instructions": "after food" } ]
    }
  ]
}

// 404 unknown phone
{ "detail": "no records found" }

// 200 with empty list if the patient exists but has no prescriptions
{ "phone": "9876543210", "name": "Asha Rao", "prescriptions": [] }
```

---

## Summary (doctor)

### GET /summary/{phone}
AI-generated medical summary. Auth required (doctor).
```json
// 200 response
{
  "phone": "9876543210",
  "name": "Asha Rao",
  "summary": "Asha is on Amoxicillin 500mg (1-0-1, 5 days) prescribed 2026-06-15 by Dr. Mehta for a likely bacterial infection. No chronic medications on record.",
  "medicine_count": 1,
  "generated_at": "2026-06-17T12:40:00Z"
}

// 200 with empty summary when zero medicines (no Gemini call made)
{ "phone": "9876543210", "name": "Asha Rao", "summary": "", "medicine_count": 0, "generated_at": null }

// 404 unknown phone
{ "detail": "no records found" }
```

---

## Errors (all endpoints)
- `400` bad input, `401` not authenticated / bad credentials, `403` wrong role,
  `404` not found, `409` conflict, `422` validation (FastAPI default), `500` server.
- Every error body: `{ "detail": "<human-readable message>" }`.

## Notes for the frontend (Lane B)
- `/upload` and `/summary/{phone}` are slow (Gemini, 5-15s). Show a loading state.
- Handle the empty-state shapes explicitly (zero medicines, unknown phone).
