"""Patient endpoints: upload prescription, view/edit/delete medicine log."""
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from ..auth import current_user, require_role
from ..config import get_settings
from ..database import get_db
from ..models import User, Prescription, Medicine, AccessLog
from ..ocr import extract_prescription
from ..schemas import (
    PrescriptionOut, MedicineOut, PatientLogOut, PrescriptionLite, PrescriptionPatch,
)

settings = get_settings()
router = APIRouter(tags=["prescriptions"])


def _rx_to_out(rx: Prescription, phone: str) -> PrescriptionOut:
    return PrescriptionOut(
        id=rx.id,
        phone=phone,
        doctor_name=rx.doctor_name,
        hospital=rx.hospital,
        date=rx.date,
        engine=rx.engine,
        confidence=rx.confidence,
        medicines=[MedicineOut.model_validate(m, from_attributes=True) for m in rx.medicines],
    )


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
    return _rx_to_out(rx, user.phone)


@router.patch("/prescription/{rx_id}", response_model=PrescriptionOut)
def patch_prescription(
    rx_id: int,
    body: PrescriptionPatch,
    user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    rx = db.get(Prescription, rx_id)
    if not rx or rx.patient_phone != user.phone:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "access denied")

    if body.doctor_name is not None:
        rx.doctor_name = body.doctor_name
    if body.hospital is not None:
        rx.hospital = body.hospital
    if body.date is not None:
        rx.date = body.date

    if body.medicines is not None:
        for m in list(rx.medicines):
            db.delete(m)
        db.flush()
        for med in body.medicines:
            db.add(Medicine(prescription_id=rx.id, **med.model_dump()))

    db.commit()
    db.refresh(rx)
    return _rx_to_out(rx, user.phone)


@router.delete("/prescription/{rx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prescription(
    rx_id: int,
    user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    rx = db.get(Prescription, rx_id)
    if not rx or rx.patient_phone != user.phone:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "access denied")

    if rx.image_path and os.path.exists(rx.image_path):
        try:
            os.unlink(rx.image_path)
        except OSError:
            pass

    db.delete(rx)
    db.commit()


@router.get("/patient/{phone}", response_model=PatientLogOut)
def patient_log(
    phone: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if user.role == "patient" and user.phone != phone:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "access denied")

    patient = db.get(User, phone)
    if not patient or patient.role != "patient":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no records found")

    # Audit log: record doctor access
    if user.role == "doctor":
        db.add(AccessLog(
            accessed_by_phone=user.phone,
            accessed_by_name=user.name,
            patient_phone=phone,
            action="view_log",
        ))
        db.commit()

    return PatientLogOut(
        phone=patient.phone,
        name=patient.name,
        prescriptions=[
            PrescriptionLite(
                id=rx.id,
                doctor_name=rx.doctor_name,
                hospital=rx.hospital,
                date=rx.date,
                image_path=rx.image_path,
                medicines=[MedicineOut.model_validate(m, from_attributes=True) for m in rx.medicines],
            )
            for rx in patient.prescriptions
        ],
    )
