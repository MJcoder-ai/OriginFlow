"""API endpoints for managing memory entries.

This route exposes a GET endpoint (`/memory`) that lists all persisted
memory records.  Each record is returned using the `Memory` Pydantic
schema, which mirrors the underlying ORM model:contentReference[oaicite:5]{index=5}.
Future enhancements may include filters, retention policies, and
creation/deletion endpoints.  A corresponding Alembic migration
(`9123abcd4567_create_memory_table.py`) must be applied to ensure the
``memory`` table exists.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session
from backend.models.memory import Memory as MemoryModel
from backend.schemas.memory import Memory as MemorySchema


router = APIRouter()


@router.get("/memory", response_model=List[MemorySchema])
async def list_memory(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
) -> List[MemorySchema]:
    """Return a paginated list of memory entries.

    This endpoint retrieves memory records from the database and
    serializes them using the ``Memory`` Pydantic model. Pagination
    parameters ``skip`` and ``limit`` can be used to page through
    results. Future enhancements may include filtering by project,
    tenant or date range.
    """

    result = await session.execute(select(MemoryModel).offset(skip).limit(limit))
    items = result.scalars().all()
    return [MemorySchema.model_validate(item) for item in items]
