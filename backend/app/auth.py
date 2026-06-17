"""Auth helpers: password hashing (bcrypt) + JWT. (eng review A4: never store plaintext)

We call the `bcrypt` library directly rather than through passlib: passlib 1.7.x is
unmaintained and breaks against bcrypt >= 4.1 (it reads the removed `__about__`
attribute). Direct use is a few lines and avoids that fragility.
"""
from datetime import datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User

settings = get_settings()
_bearer = HTTPBearer(auto_error=True)


def hash_password(raw: str) -> str:
    # bcrypt hard-caps the input at 72 bytes; truncate explicitly so longer
    # passwords don't raise (they hash on the first 72 bytes, standard behavior).
    return bcrypt.hashpw(raw.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def make_token(phone: str, role: str) -> str:
    payload = {
        "sub": phone,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(
            creds.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        phone = payload.get("sub")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token")
    user = db.get(User, phone)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user


def require_role(role: str):
    """Dependency factory: enforce a user role on an endpoint."""
    def _dep(user: User = Depends(current_user)) -> User:
        if user.role != role:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"{role} access required")
        return user
    return _dep
