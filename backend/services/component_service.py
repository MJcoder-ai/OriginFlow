# backend/services/component_service.py
"""Business logic for components."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

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
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
