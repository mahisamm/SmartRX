"""Seed the database with demo users + prescriptions for a live demo / screenshots.

Run from the backend/ dir (with the venv active):
    python seed.py

Idempotent: wipes the demo rows it owns and re-inserts them. Safe to re-run.

Demo logins (all password: "demo1234"):
    Doctor   ->  phone 9000000001
    Patient  ->  phone 9876543210  (Asha Rao, 2 prescriptions)
    Patient  ->  phone 9123456780  (Ravi Kumar, 1 prescription)
    Patient  ->  phone 9555500000  (Meena Iyer, no prescriptions — empty-state demo)
"""
from datetime import date

from app.database import Base, engine, SessionLocal
from app import models  # noqa: F401  (register models before create_all)
from app.auth import hash_password
from app.models import User, Prescription, Medicine

DEMO_PASSWORD = "demo1234"

USERS = [
    {"phone": "9000000001", "name": "Dr. Priya Nair", "role": "doctor"},
    {"phone": "9876543210", "name": "Asha Rao", "role": "patient"},
    {"phone": "9123456780", "name": "Ravi Kumar", "role": "patient"},
    {"phone": "9555500000", "name": "Meena Iyer", "role": "patient"},
]

PRESCRIPTIONS = [
    {
        "patient_phone": "9876543210",
        "doctor_name": "Dr. Mehta",
        "hospital": "City Clinic",
        "date": date(2026, 6, 15),
        "engine": "tesseract+gemini",
        "confidence": 0.91,
        "medicines": [
            {"name": "Amoxicillin", "dose": "500mg", "frequency": "1-0-1",
             "duration": "5 days", "instructions": "after food"},
            {"name": "Paracetamol", "dose": "650mg", "frequency": "SOS",
             "duration": "3 days", "instructions": "if fever above 100F"},
        ],
    },
    {
        "patient_phone": "9876543210",
        "doctor_name": "Dr. Saxena",
        "hospital": "Apollo",
        "date": date(2026, 5, 2),
        "engine": "gemini_vision",
        "confidence": 0.78,
        "medicines": [
            {"name": "Cetirizine", "dose": "10mg", "frequency": "0-0-1",
             "duration": "10 days", "instructions": "at night"},
        ],
    },
    {
        "patient_phone": "9123456780",
        "doctor_name": "Dr. Mehta",
        "hospital": "City Clinic",
        "date": date(2026, 6, 10),
        "engine": "gemini_vision",
        "confidence": 0.83,
        "medicines": [
            {"name": "Metformin", "dose": "500mg", "frequency": "1-0-1",
             "duration": "30 days", "instructions": "with meals"},
            {"name": "Atorvastatin", "dose": "10mg", "frequency": "0-0-1",
             "duration": "30 days", "instructions": "at bedtime"},
        ],
    },
]


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        demo_phones = [u["phone"] for u in USERS]
        # Clean prior demo rows (cascade clears their prescriptions + medicines).
        for u in db.query(User).filter(User.phone.in_(demo_phones)).all():
            db.delete(u)
        db.commit()

        for u in USERS:
            db.add(User(
                phone=u["phone"], name=u["name"], role=u["role"],
                password_hash=hash_password(DEMO_PASSWORD),
            ))
        db.commit()

        for p in PRESCRIPTIONS:
            rx = Prescription(
                patient_phone=p["patient_phone"],
                doctor_name=p["doctor_name"],
                hospital=p["hospital"],
                date=p["date"],
                engine=p["engine"],
                confidence=p["confidence"],
                medicines=[Medicine(**m) for m in p["medicines"]],
            )
            db.add(rx)
        db.commit()

        print(f"Seeded {len(USERS)} users and {len(PRESCRIPTIONS)} prescriptions.")
        print(f"All demo passwords: {DEMO_PASSWORD!r}")
        print("Doctor login: 9000000001  |  Patients: 9876543210, 9123456780, 9555500000")
    finally:
        db.close()


if __name__ == "__main__":
    run()
