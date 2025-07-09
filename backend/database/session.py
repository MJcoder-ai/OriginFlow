# backend/database/session.py
"""Async database session factory.

Creates the SQLAlchemy async engine and session dependency.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import settings


engine = create_async_engine(settings.database_url, future=True)
SessionMaker = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` for request-scoped use."""

    async with SessionMaker() as session:
        yield session
