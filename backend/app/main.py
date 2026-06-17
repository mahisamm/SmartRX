"""FastAPI app entry. Creates tables, mounts routers, enables CORS for the React dev server."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from . import models  # noqa: F401  (register models on Base before create_all)
from .routers import auth_router, prescriptions_router, summary_router

# Day 1: create tables directly. Day 5+: switch to Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="smartRX API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(prescriptions_router.router)
app.include_router(summary_router.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
