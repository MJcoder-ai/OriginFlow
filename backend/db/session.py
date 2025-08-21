"""Synchronous SQLAlchemy engine for admin/utility paths.

Hardened for SQLite so test/dev behave predictably:
 - File-backed DBs "just work"
 - In-memory DBs use ``StaticPool`` so all connections share one DB
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import settings

# Use synchronous variant of the database URL (strip async driver if present)
DATABASE_URL = settings.database_url.replace("+aiosqlite", "")

# If file-backed SQLite, ensure parent directory exists
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "", 1)
    if not db_path.startswith("file::"):
        Path(os.path.dirname(db_path) or ".").mkdir(parents=True, exist_ok=True)

engine_kwargs: dict[str, object] = {"future": True}

if DATABASE_URL.startswith("sqlite"):
    connect_args: dict[str, object] = {"check_same_thread": False}
    # For in-memory SQLite, use StaticPool so all connections share one DB
    # Covers both ":memory:" and "file::memory:?cache=shared"
    if ":memory:" in DATABASE_URL:
        engine_kwargs["poolclass"] = StaticPool
        # If URI form is used, let SQLite parse it
        if DATABASE_URL.startswith("sqlite:///file:"):
            connect_args["uri"] = True
    engine_kwargs["connect_args"] = connect_args

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
