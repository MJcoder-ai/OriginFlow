"""API endpoints for querying the component master library.

This module exposes a search endpoint that allows the frontend or other
services to discover available components in the master database. Clients
can filter by category, manufacturer and a power range. The route returns a
list of ``ComponentMasterInDB`` objects.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session
from backend.schemas.component_master import ComponentMasterInDB
from backend.services.component_db_service import ComponentDBService


router = APIRouter()


@router.get(
    "/component-library/search",
    response_model=List[ComponentMasterInDB],
    summary="Search the component master library",
    tags=["components"],
)
async def search_component_library(
    category: Optional[str] = None,
    manufacturer: Optional[str] = None,
    min_power: Optional[float] = None,
    max_power: Optional[float] = None,
    session: AsyncSession = Depends(get_session),
) -> List[ComponentMasterInDB]:
    """Return components from the master library filtered by optional criteria."""

    service = ComponentDBService(session)
    results = await service.search(
        category=category,
        manufacturer=manufacturer,
        min_power=min_power,
        max_power=max_power,
    )
    return [ComponentMasterInDB.model_validate(obj) for obj in results]

