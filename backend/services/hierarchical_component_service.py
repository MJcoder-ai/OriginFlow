"""Service layer for hierarchical component records."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import SessionMaker
from backend.models.component_hierarchy import HierarchicalComponent


class HierarchicalComponentService:
    """Provides queries over hierarchical component records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(self, domain: Optional[str] = None) -> List[HierarchicalComponent]:
        """Return components filtered by domain if provided."""
        stmt = select(HierarchicalComponent)
        if domain:
            stmt = stmt.where(
                or_(
                    HierarchicalComponent.domain.like(f'%"{domain}"%'),
                    HierarchicalComponent.domain.like(f'%{domain},%'),
                )
            )
        result = await self.session.execute(stmt)
        return result.scalars().all()


async def get_hierarchical_component_service() -> HierarchicalComponentService:
    """FastAPI dependency provider for :class:`HierarchicalComponentService`."""
    async with SessionMaker() as session:
        yield HierarchicalComponentService(session)

