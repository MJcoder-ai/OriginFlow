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

        obj = Component(id=generate_id("component"), **data.model_dump())
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


async def find_component_by_name(name: str) -> Component | None:
    """Return first component matching ``name`` case-insensitively."""

    async with SessionMaker() as session:
        stmt = select(Component).where(Component.name.ilike(name)).limit(1)
        result = await session.execute(stmt)
        return result.scalars().first()
