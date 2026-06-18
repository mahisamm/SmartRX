"""Audit log endpoint — patients see who accessed their data."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import current_user
from ..database import get_db
from ..models import User, AccessLog
from ..schemas import AuditEntry, AuditLogOut

router = APIRouter(tags=["audit"])


@router.get("/audit-log", response_model=AuditLogOut)
def get_audit_log(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if user.role == "patient":
        rows = (
            db.query(AccessLog)
            .filter(AccessLog.patient_phone == user.phone)
            .order_by(AccessLog.accessed_at.desc())
            .limit(100)
            .all()
        )
    else:
        rows = (
            db.query(AccessLog)
            .filter(AccessLog.accessed_by_phone == user.phone)
            .order_by(AccessLog.accessed_at.desc())
            .limit(100)
            .all()
        )

    return AuditLogOut(
        entries=[
            AuditEntry(
                id=r.id,
                accessed_by_name=r.accessed_by_name,
                accessed_by_phone=r.accessed_by_phone,
                patient_phone=r.patient_phone,
                action=r.action,
                accessed_at=r.accessed_at,
            )
            for r in rows
        ]
    )
