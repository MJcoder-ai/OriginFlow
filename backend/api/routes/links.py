# backend/api/routes/links.py
"""CRUD routes for links between components."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session
from backend.models.link import Link as LinkModel
from backend.schemas.link import Link, LinkCreate
from backend.services.link_service import LinkService

router = APIRouter()


@router.post("/links/", response_model=Link)
async def create_link(link: LinkCreate, session: AsyncSession = Depends(get_session)) -> Link:
    """Create and persist a link between components."""

    service = LinkService(session)
    obj = await service.create(link)
    return Link.model_validate(obj)


@router.get("/links/", response_model=List[Link])
async def read_links(
    skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session)
) -> List[Link]:
    """Return a paginated list of links."""

    result = await session.execute(select(LinkModel).offset(skip).limit(limit))
    items = result.scalars().all()
    return [Link.model_validate(item) for item in items]


@router.get("/links/{link_id}", response_model=Link)
async def read_link(link_id: str, session: AsyncSession = Depends(get_session)) -> Link:
    """Return a single link by its ID."""

    result = await session.get(LinkModel, link_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Link not found")
    return Link.model_validate(result)


@router.patch("/links/{link_id}", response_model=Link)
async def update_link(
    link_id: str, update: dict, session: AsyncSession = Depends(get_session)
) -> Link:
    """Update an existing link, merging path and lock metadata."""

    obj = await session.get(LinkModel, link_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Link not found")

    path = update.pop("path_by_layer", None)
    locked = update.pop("locked_in_layers", None)
    for key, value in update.items():
        setattr(obj, key, value)
    if path:
        merged = obj.path_by_layer or {}
        merged.update(path)
        obj.path_by_layer = merged
    if locked:
        merged_locks = obj.locked_in_layers or {}
        merged_locks.update(locked)
        obj.locked_in_layers = merged_locks

    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return Link.model_validate(obj)
