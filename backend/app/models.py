"""SQLAlchemy ORM models — the DB schema.

    users (phone PK) 1───many prescriptions 1───many medicines

Phone number is the patient identity (per design doc). Doctors are also users,
distinguished by `role`.
"""
from datetime import datetime, date, timezone

from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    phone: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # "patient" | "doctor"
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    prescriptions: Mapped[list["Prescription"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="Prescription.created_at.desc()",
    )


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_phone: Mapped[str] = mapped_column(
        ForeignKey("users.phone"), index=True, nullable=False
    )
    doctor_name: Mapped[str | None] = mapped_column(String(120))
    hospital: Mapped[str | None] = mapped_column(String(160))
    date: Mapped[date | None] = mapped_column(Date)
    image_path: Mapped[str | None] = mapped_column(String(255))
    engine: Mapped[str | None] = mapped_column(String(40))   # extraction engine used
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    patient: Mapped["User"] = relationship(back_populates="prescriptions")
    medicines: Mapped[list["Medicine"]] = relationship(
        back_populates="prescription", cascade="all, delete-orphan"
    )


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prescription_id: Mapped[int] = mapped_column(
        ForeignKey("prescriptions.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    dose: Mapped[str | None] = mapped_column(String(60))
    frequency: Mapped[str | None] = mapped_column(String(60))
    duration: Mapped[str | None] = mapped_column(String(60))
    instructions: Mapped[str | None] = mapped_column(Text)

    prescription: Mapped["Prescription"] = relationship(back_populates="medicines")


class AccessLog(Base):
    """Audit trail — every doctor lookup of a patient is recorded."""
    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    accessed_by_phone: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    accessed_by_name: Mapped[str] = mapped_column(String(120), nullable=False)
    patient_phone: Mapped[str] = mapped_column(String(20), ForeignKey("users.phone"), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # "view_log" | "view_summary"
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DoctorNote(Base):
    """Private notes a doctor adds after consulting a patient."""
    __tablename__ = "doctor_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doctor_phone: Mapped[str] = mapped_column(String(20), ForeignKey("users.phone"), index=True, nullable=False)
    patient_phone: Mapped[str] = mapped_column(String(20), ForeignKey("users.phone"), index=True, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class UserSettings(Base):
    """Per-user preferences: language, notification prefs, doctor profile."""
    __tablename__ = "user_settings"

    phone: Mapped[str] = mapped_column(String(20), ForeignKey("users.phone"), primary_key=True)
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="en")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reminder_time: Mapped[str] = mapped_column(String(5), nullable=False, default="08:00")
    hospital_name: Mapped[str | None] = mapped_column(String(160))
    specialization: Mapped[str | None] = mapped_column(String(100))
