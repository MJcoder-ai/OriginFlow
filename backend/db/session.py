"""Synchronous database session helpers."""
from __future__ import annotations

from sqlalchemy import create_engine
from typing import Generator
from sqlalchemy.orm import sessionmaker, Session

from backend.config import settings

# Use synchronous variant of the database URL (strip async driver if present)
DATABASE_URL = settings.database_url.replace("+aiosqlite", "")
engine = create_engine(
    DATABASE_URL,
    future=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
