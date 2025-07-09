# backend/api/routes/components.py
"""CRUD routes for components."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.api.deps import get_session
from backend.models.component import Component as ComponentModel
from backend.schemas.component import (
    Component as ComponentSchema,
    ComponentCreate,
    ComponentUpdate,
)
from backend.services.component_service import ComponentService

router = APIRouter()


@router.post("/components/", response_model=ComponentSchema)
async def create_component(
    component: ComponentCreate, session: AsyncSession = Depends(get_session)
) -> ComponentSchema:
    """Create and persist a new component."""

    service = ComponentService(session)
    obj = await service.create(component)
    return ComponentSchema.model_validate(obj)


@router.get("/components/", response_model=List[ComponentSchema])
async def read_components(
    skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session)
) -> List[ComponentSchema]:
    """Return a paginated list of components."""

    stmt = select(ComponentModel).offset(skip).limit(limit)
    result = await session.execute(stmt)
    items = result.scalars().all()
    return [ComponentSchema.model_validate(item) for item in items]

@router.get("/components/{component_id}", response_model=ComponentSchema)
async def read_component(
    component_id: str, session: AsyncSession = Depends(get_session)
) -> ComponentSchema:
    """Return a single component by its ID."""

    result = await session.get(ComponentModel, component_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Component not found")
    return ComponentSchema.model_validate(result)


@router.patch("/components/{component_id}", response_model=ComponentSchema)
async def update_component(
    component_id: str,
    component: ComponentUpdate,
    session: AsyncSession = Depends(get_session),
) -> ComponentSchema:
    result = await session.get(ComponentModel, component_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Component not found")
    for key, value in component.model_dump(exclude_unset=True).items():
        setattr(result, key, value)
    session.add(result)
    await session.commit()
    await session.refresh(result)
    return ComponentSchema.model_validate(result)


@router.delete("/components/{component_id}", status_code=204)
async def delete_component(
    component_id: str, session: AsyncSession = Depends(get_session)
) -> Response:
    """Delete a component and return ``204 No Content`` on success."""

    result = await session.get(ComponentModel, component_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Component not found")
    await session.delete(result)
    await session.commit()
    return Response(status_code=204)
