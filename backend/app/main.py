"""FastAPI app entry. Creates tables, mounts routers, enables CORS."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import Base, engine
from . import models  # noqa: F401  (register models on Base before create_all)
from .routers import auth_router, prescriptions_router, summary_router

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="smartRX API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(prescriptions_router.router)
app.include_router(summary_router.router)

# Serve uploaded prescription images under /uploads/<filename>.
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
