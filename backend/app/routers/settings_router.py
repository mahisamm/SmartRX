"""User settings endpoints — get and update per-user preferences."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import current_user
from ..database import get_db
from ..models import User, UserSettings
from ..schemas import SettingsPatch, SettingsOut

router = APIRouter(tags=["settings"])


def _get_or_create_settings(phone: str, db: Session) -> UserSettings:
    s = db.get(UserSettings, phone)
    if not s:
        s = UserSettings(phone=phone)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def _to_out(s: UserSettings) -> SettingsOut:
    return SettingsOut(
        language=s.language,
        notifications_enabled=s.notifications_enabled,
        reminder_time=s.reminder_time,
        hospital_name=s.hospital_name,
        specialization=s.specialization,
    )


@router.get("/settings", response_model=SettingsOut)
def get_settings(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return _to_out(_get_or_create_settings(user.phone, db))


@router.patch("/settings", response_model=SettingsOut)
def update_settings(
    body: SettingsPatch,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    s = _get_or_create_settings(user.phone, db)

    if body.language is not None:
        s.language = body.language
    if body.notifications_enabled is not None:
        s.notifications_enabled = body.notifications_enabled
    if body.reminder_time is not None:
        s.reminder_time = body.reminder_time
    if body.hospital_name is not None:
        s.hospital_name = body.hospital_name
    if body.specialization is not None:
        s.specialization = body.specialization

    db.commit()
    db.refresh(s)
    return _to_out(s)
