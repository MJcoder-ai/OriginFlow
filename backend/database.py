# backend/database.py
"""Database connection utilities.

Creates the SQLAlchemy engine and session factory for request-scoped sessions.
"""

from __future__ import annotations

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./originflow.db")

# When running with the default SQLite database, allow connections to be shared
# across threads. This prevents request handlers from blocking each other when
# they access the database concurrently.
engine_kwargs: dict[str, object] = {"future": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
