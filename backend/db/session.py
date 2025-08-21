"""Synchronous database session helpers."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from typing import Generator
from sqlalchemy.orm import sessionmaker, Session

from backend.config import settings

# Use synchronous variant of the database URL (strip async driver if present)
DATABASE_URL = settings.database_url.replace("+aiosqlite", "")
engine_kwargs = {"future": True}

if DATABASE_URL.startswith("sqlite") and DATABASE_URL.endswith(":memory:"):
    # Share the same in-memory database across sessions/threads,
    # mirroring async engine's StaticPool usage.
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    })
elif DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({"connect_args": {"check_same_thread": False}})

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
