"""Pydantic schemas — request/response shapes + LLM-output validation.

The MedicineOut / ExtractionResult models double as the guard against malformed
Gemini JSON (eng review finding: validate LLM output before it touches the DB).
"""
import datetime as dt
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---- auth ----
class RegisterIn(BaseModel):
    phone: str = Field(min_length=5, max_length=20)
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=4, max_length=128)
    role: Literal["patient", "doctor"]


class LoginIn(BaseModel):
    phone: str
    password: str


class UserOut(BaseModel):
    phone: str
    name: str
    role: str


class AuthOut(BaseModel):
    token: str
    user: UserOut


# ---- medicines / prescriptions ----
class MedicineOut(BaseModel):
    name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None


class ExtractionResult(BaseModel):
    """What the OCR/AI layer returns. Validates raw Gemini JSON."""
    doctor_name: Optional[str] = None
    hospital: Optional[str] = None
    date: Optional[dt.date] = None
    engine: str
    confidence: Optional[float] = None
    medicines: list[MedicineOut] = []


class PrescriptionOut(BaseModel):
    id: int
    phone: str
    doctor_name: Optional[str] = None
    hospital: Optional[str] = None
    date: Optional[dt.date] = None
    engine: Optional[str] = None
    confidence: Optional[float] = None
    medicines: list[MedicineOut] = []


class PrescriptionLite(BaseModel):
    id: int
    doctor_name: Optional[str] = None
    hospital: Optional[str] = None
    date: Optional[dt.date] = None
    medicines: list[MedicineOut] = []


class PatientLogOut(BaseModel):
    phone: str
    name: str
    prescriptions: list[PrescriptionLite] = []


class SummaryOut(BaseModel):
    phone: str
    name: str
    summary: str
    medicine_count: int
    generated_at: Optional[dt.datetime] = None
