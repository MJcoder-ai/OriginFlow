"""
Async SQLAlchemy engine/session for API routes.
SQLite is configured to be robust in dev/test:
 - File-backed DB: auto-create parent directory to avoid open errors
 - In-memory DB: ``StaticPool`` so ``uvicorn --reload`` / multiple connections share one DB
"""
from __future__ import annotations

import os
from pathlib import Path
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import settings

ASYNC_DATABASE_URL = settings.database_url

# If file-backed SQLite, ensure parent directory exists
if ASYNC_DATABASE_URL.startswith("sqlite+aiosqlite:///"):
    db_path = ASYNC_DATABASE_URL.replace("sqlite+aiosqlite:///", "", 1)
    if not db_path.startswith("file::"):
        Path(os.path.dirname(db_path) or ".").mkdir(parents=True, exist_ok=True)

# Configure connect args / pool for SQLite variants
connect_args: dict[str, object] = {}
engine_kwargs: dict[str, object] = {"future": True}
if ASYNC_DATABASE_URL.startswith("sqlite+aiosqlite"):
    connect_args = {"check_same_thread": False}
    # Share in-memory DB across connections (including --reload)
    if ":memory:" in ASYNC_DATABASE_URL:
        engine_kwargs["poolclass"] = StaticPool
        if ASYNC_DATABASE_URL.startswith("sqlite+aiosqlite:///file:"):
            connect_args["uri"] = True

# Canonical async engine (renamed for clarity). Keep `engine` alias for b/w compat.
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionMaker = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionMaker() as session:
        yield session

# --- Backward-compatibility alias (do not remove without repo-wide replace) ---
# Some older modules may import `engine` symbol; keep it pointing at async engine.
engine = async_engine

__all__ = ["async_engine", "engine", "SessionMaker", "get_session"]

