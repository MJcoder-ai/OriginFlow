# backend/services/component_service.py
"""Business logic for components."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from backend.database.session import SessionMaker

from fastapi import HTTPException

from backend.models.component import Component
from backend.schemas.component import ComponentCreate
from backend.utils.id import generate_id


class ComponentService:
    """Service layer for component CRUD."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: ComponentCreate) -> Component:
        """Persist a new component and return it."""

        comp_id = data.id or generate_id("component")
        payload = data.model_dump(exclude_none=True)
        payload.pop("id", None)
        obj = Component(id=comp_id, **payload)
        self.session.add(obj)
        try:
            await self.session.commit()
        except IntegrityError as err:
            await self.session.rollback()
            # duplicate standard_code -> fall back to generated code
            if "UNIQUE constraint failed: components.standard_code" in str(err):
                obj.standard_code = f"AUTO-{generate_id('').split('_')[1][:6]}"
                self.session.add(obj)
                await self.session.commit()
            else:
                raise HTTPException(409, "Component already exists") from err
        await self.session.refresh(obj)
        return obj

    async def list(self, skip: int = 0, limit: int = 100) -> list[Component]:
        """Return a paginated list of components."""
        stmt = select(Component).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, component_id: str) -> Component | None:
        """Return a component by id or None."""
        stmt = select(Component).where(Component.id == component_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update(self, component_id: str, data: dict) -> Component:
        """Update fields on a component and persist changes."""
        obj = await self.get(component_id)
        if not obj:
            raise HTTPException(404, "Component not found")
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, component_id: str) -> None:
        """Delete a component by id."""
        obj = await self.get(component_id)
        if not obj:
            raise HTTPException(404, "Component not found")
        await self.session.delete(obj)
        await self.session.commit()


async def find_component_by_name(name: str) -> Component | None:
    """Return first component matching ``name`` case-insensitively."""

    async with SessionMaker() as session:
        stmt = select(Component).where(Component.name.ilike(name)).limit(1)
        result = await session.execute(stmt)
        return result.scalars().first()
