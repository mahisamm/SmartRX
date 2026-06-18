"""Doctor notes endpoints — add and retrieve consultation notes per patient."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import current_user, require_role
from ..database import get_db
from ..models import User, DoctorNote
from ..schemas import NoteIn, NoteOut, NotesListOut

router = APIRouter(tags=["notes"])


@router.post(
    "/patient/{phone}/notes",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
)
def add_note(
    phone: str,
    body: NoteIn,
    doctor: User = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
):
    patient = db.get(User, phone)
    if not patient or patient.role != "patient":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no records found")

    note = DoctorNote(
        doctor_phone=doctor.phone,
        patient_phone=phone,
        note=body.note,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return NoteOut(
        id=note.id,
        note=note.note,
        created_at=note.created_at,
        doctor_name=doctor.name,
    )


@router.get("/patient/{phone}/notes", response_model=NotesListOut)
def get_notes(
    phone: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    # Patients see their own notes; doctors see notes for any patient they look up.
    if user.role == "patient" and user.phone != phone:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "access denied")

    patient = db.get(User, phone)
    if not patient or patient.role != "patient":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no records found")

    rows = (
        db.query(DoctorNote)
        .filter(DoctorNote.patient_phone == phone)
        .order_by(DoctorNote.created_at.desc())
        .all()
    )

    result = []
    for n in rows:
        doc = db.get(User, n.doctor_phone)
        result.append(
            NoteOut(
                id=n.id,
                note=n.note,
                created_at=n.created_at,
                doctor_name=doc.name if doc else "Unknown",
            )
        )

    return NotesListOut(notes=result)
