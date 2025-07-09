# backend/services/link_service.py
"""Business logic for links."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.link import Link
from backend.schemas.link import LinkCreate
from backend.utils.id import generate_id


class LinkService:
    """Service layer for link CRUD."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: LinkCreate) -> Link:
        """Persist a new link and return it."""

        obj = Link(id=generate_id("link"), **data.model_dump())
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
