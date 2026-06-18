"""Auth endpoints: register + login."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import hash_password, verify_password, make_token
from ..database import get_db
from ..models import User, UserSettings
from ..schemas import RegisterIn, LoginIn, AuthOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.get(User, body.phone):
        raise HTTPException(status.HTTP_409_CONFLICT, "phone already registered")
    user = User(
        phone=body.phone,
        name=body.name,
        role=body.role,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.flush()

    # Auto-create settings row; seed doctor profile fields if provided
    user_settings = UserSettings(
        phone=body.phone,
        hospital_name=body.hospital_name if body.role == "doctor" else None,
        specialization=body.specialization if body.role == "doctor" else None,
    )
    db.add(user_settings)
    db.commit()

    return AuthOut(
        token=make_token(user.phone, user.role),
        user=UserOut(phone=user.phone, name=user.name, role=user.role),
    )


@router.post("/login", response_model=AuthOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.get(User, body.phone)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid phone or password")
    return AuthOut(
        token=make_token(user.phone, user.role),
        user=UserOut(phone=user.phone, name=user.name, role=user.role),
    )
