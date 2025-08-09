# backend/database/session.py
"""Async database session factory.

Creates the SQLAlchemy async engine and session dependency.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.config import settings


# Provide SQLite-specific options to reduce "database is locked" errors when
# multiple requests access the database concurrently. Using ``StaticPool`` keeps
# a single connection shared across the app and ``timeout`` allows SQLite to
# wait for locks to clear instead of immediately raising ``OperationalError``.
engine_kwargs: dict[str, object] = {"future": True}
if settings.database_url.startswith("sqlite"):
    engine_kwargs.update(
        {
            "connect_args": {"check_same_thread": False, "timeout": 30},
            "poolclass": StaticPool,
        }
    )

engine = create_async_engine(settings.database_url, **engine_kwargs)
SessionMaker = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` for request-scoped use."""

    async with SessionMaker() as session:
        yield session
