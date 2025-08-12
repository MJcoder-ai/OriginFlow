"""Service layer for hierarchical component records."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, or_, func, text
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
            # Use parameterized queries to prevent SQL injection
            # For JSON arrays, use proper JSON functions
            stmt = stmt.where(
                or_(
                    # Check if domain is contained in the JSON array
                    func.json_extract(HierarchicalComponent.domain, '$[*]').contains(domain),
                    # Alternative: check if domain matches any array element
                    func.json_search(HierarchicalComponent.domain, 'one', domain).is_not(None)
                )
            )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def search_safe(self, domain: Optional[str] = None, limit: int = 100) -> List[HierarchicalComponent]:
        """Safe search with input validation and limits."""
        stmt = select(HierarchicalComponent)
        
        if domain:
            # Validate input - only allow alphanumeric and common characters
            if not domain.replace(' ', '').replace('-', '').replace('_', '').isalnum():
                raise ValueError("Invalid domain search term")
            
            # Limit search term length
            if len(domain) > 50:
                raise ValueError("Domain search term too long")
            
            # Use proper parameterized query
            stmt = stmt.where(
                HierarchicalComponent.domain.contains(domain)
            )
        
        # Always apply a reasonable limit
        stmt = stmt.limit(min(limit, 1000))
        
        result = await self.session.execute(stmt)
        return result.scalars().all()


async def get_hierarchical_component_service() -> HierarchicalComponentService:
    """FastAPI dependency provider for :class:`HierarchicalComponentService`."""
    async with SessionMaker() as session:
        yield HierarchicalComponentService(session)

