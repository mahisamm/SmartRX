"""SQLAlchemy ORM models — the DB schema.

    users (phone PK) 1───many prescriptions 1───many medicines

Phone number is the patient identity (per design doc). Doctors are also users,
distinguished by `role`.
"""
from datetime import datetime, date, timezone

from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, Text
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
