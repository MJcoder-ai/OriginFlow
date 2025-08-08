"""API endpoints for managing memory entries.

Exposes a simple GET endpoint to list memory entries. Additional
functionality such as deletion and retention policies can be layered
on later. This route uses the async SQLAlchemy session provided by
``get_session`` to fetch records from the ``memory`` table.
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
