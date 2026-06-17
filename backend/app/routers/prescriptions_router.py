"""Patient endpoints: upload a prescription, view medicine log."""
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from ..auth import current_user, require_role
from ..config import get_settings
from ..database import get_db
from ..models import User, Prescription, Medicine
from ..ocr import extract_prescription
from ..schemas import PrescriptionOut, MedicineOut, PatientLogOut, PrescriptionLite

settings = get_settings()
router = APIRouter(tags=["prescriptions"])


@router.post("/upload", response_model=PrescriptionOut, status_code=status.HTTP_201_CREATED)
async def upload_prescription(
    file: UploadFile = File(...),
    user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    if file.content_type not in settings.allowed_image_types:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "file must be a JPEG or PNG image")

    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "image exceeds 10MB limit")

    try:
        result = extract_prescription(data, file.content_type)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "could not read prescription image")

    # Persist image (eng review A3: local disk is ephemeral on free tiers — fine for demo).
    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = ".png" if "png" in (file.content_type or "") else ".jpg"
    image_path = os.path.join(settings.upload_dir, f"{uuid.uuid4().hex}{ext}")
    with open(image_path, "wb") as fh:
        fh.write(data)

    rx = Prescription(
        patient_phone=user.phone,
        doctor_name=result.doctor_name,
        hospital=result.hospital,
        date=result.date,
        image_path=image_path,
        engine=result.engine,
        confidence=result.confidence,
        medicines=[Medicine(**m.model_dump()) for m in result.medicines],
    )
    db.add(rx)
    db.commit()
    db.refresh(rx)

    return PrescriptionOut(
        id=rx.id,
        phone=user.phone,
        doctor_name=rx.doctor_name,
        hospital=rx.hospital,
        date=rx.date,
        engine=rx.engine,
        confidence=rx.confidence,
        medicines=[MedicineOut.model_validate(m, from_attributes=True) for m in rx.medicines],
    )


@router.get("/patient/{phone}", response_model=PatientLogOut)
def patient_log(
    phone: str,
    _user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    patient = db.get(User, phone)
    if not patient or patient.role != "patient":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no records found")

    return PatientLogOut(
        phone=patient.phone,
        name=patient.name,
        prescriptions=[
            PrescriptionLite(
                id=rx.id,
                doctor_name=rx.doctor_name,
                hospital=rx.hospital,
                date=rx.date,
                medicines=[MedicineOut.model_validate(m, from_attributes=True) for m in rx.medicines],
            )
            for rx in patient.prescriptions
        ],
    )
