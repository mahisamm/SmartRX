"""Doctor endpoint: AI-generated patient summary."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import require_role
from ..database import get_db
from ..models import User
from ..schemas import SummaryOut
from ..gemini_client import generate_summary

router = APIRouter(tags=["summary"])


@router.get("/summary/{phone}", response_model=SummaryOut)
def patient_summary(
    phone: str,
    _doctor: User = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
):
    patient = db.get(User, phone)
    if not patient or patient.role != "patient":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no records found")

    prescriptions = [
        {
            "doctor_name": rx.doctor_name,
            "date": str(rx.date) if rx.date else None,
            "medicines": [
                {"name": m.name, "dose": m.dose, "frequency": m.frequency,
                 "duration": m.duration, "instructions": m.instructions}
                for m in rx.medicines
            ],
        }
        for rx in patient.prescriptions
    ]
    med_count = sum(len(p["medicines"]) for p in prescriptions)

    # Zero medicines: skip the Gemini call entirely (eng review perf finding).
    if med_count == 0:
        return SummaryOut(phone=patient.phone, name=patient.name, summary="",
                          medicine_count=0, generated_at=None)

    summary = generate_summary(patient.name, prescriptions)
    return SummaryOut(
        phone=patient.phone,
        name=patient.name,
        summary=summary,
        medicine_count=med_count,
        generated_at=datetime.utcnow(),
    )
