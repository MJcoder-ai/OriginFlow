"""Service layer for the component master database.

This service provides high-level operations for reading and writing master
component records.  It acts as a single source of truth for component
specifications aggregated from supplier APIs and parsed datasheets.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from backend.database.session import SessionMaker
from backend.models.component_master import ComponentMaster
from backend.schemas.component_master import ComponentMasterCreate


class ComponentDBService:
    """Service for CRUD operations on the component master table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: ComponentMasterCreate) -> ComponentMaster:
        """Persist a new component master record and return it."""
        obj = ComponentMaster(**data.model_dump())
        self.session.add(obj)
        try:
            await self.session.commit()
        except IntegrityError as err:
            await self.session.rollback()
            if "UNIQUE constraint failed" in str(err):
                raise HTTPException(409, "Component master with this part number already exists") from err
            raise
        await self.session.refresh(obj)
        return obj

    async def bulk_create(self, items: List[ComponentMasterCreate]) -> List[ComponentMaster]:
        """Bulk insert multiple master records."""
        objs = [ComponentMaster(**i.model_dump()) for i in items]
        self.session.add_all(objs)
        try:
            await self.session.commit()
        except IntegrityError as err:
            await self.session.rollback()
            raise HTTPException(409, "Error inserting component masters") from err
        for obj in objs:
            await self.session.refresh(obj)
        return objs

    async def get_by_part_number(self, part_number: str) -> Optional[ComponentMaster]:
        """Retrieve a component master by part number."""
        stmt = select(ComponentMaster).where(ComponentMaster.part_number == part_number)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def search(self, category: Optional[str] = None, manufacturer: Optional[str] = None,
                     min_power: Optional[float] = None, max_power: Optional[float] = None) -> List[ComponentMaster]:
        """Search components by category, manufacturer and power range."""
        stmt = select(ComponentMaster)
        if category:
            stmt = stmt.where(ComponentMaster.category == category)
        if manufacturer:
            stmt = stmt.where(ComponentMaster.manufacturer == manufacturer)
        if min_power is not None:
            stmt = stmt.where(ComponentMaster.power >= min_power)
        if max_power is not None:
            stmt = stmt.where(ComponentMaster.power <= max_power)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_part_number(self, part_number: str) -> int:
        """Delete all records with a matching part number.

        This method removes components identified by their manufacturer part
        number from the component master table.  It is intended for
        development and cleanup scenarios where a specific record needs to
        be removed without clearing the entire table.  The number of rows
        deleted is returned.
        """
        stmt = delete(ComponentMaster).where(ComponentMaster.part_number == part_number)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount


async def get_component_db_service() -> ComponentDBService:
    """FastAPI dependency injection helper to provide a service instance."""
    async with SessionMaker() as session:
        yield ComponentDBService(session)

