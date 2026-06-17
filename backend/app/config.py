"""App configuration. Reads from environment / .env."""
import os
from functools import lru_cache


class Settings:
    # SQLite for dev (zero setup). Swap to a Postgres URL for prod:
    #   postgresql+psycopg://user:pass@host:5432/smartrx
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./smartrx.db")

    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24h

    # Gemini
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # Uploads
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))  # 10MB
    allowed_image_types: tuple = ("image/jpeg", "image/png", "image/jpg")

    # OCR fallback: trust Gemini vision when Tesseract mean word-confidence is below this.
    tesseract_confidence_floor: float = float(os.getenv("TESSERACT_CONF_FLOOR", "60"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
