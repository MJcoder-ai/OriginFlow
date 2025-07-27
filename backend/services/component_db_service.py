"""CRUD service for the ComponentMaster table."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from backend.database.session import SessionMaker
from backend.models.component_master import ComponentMaster
from backend.schemas.component_master import ComponentMasterCreate


class ComponentDBService:
    """Service providing operations on component master records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: ComponentMasterCreate) -> ComponentMaster:
        obj = ComponentMaster(**data.model_dump())
        self.session.add(obj)
        try:
            await self.session.commit()
        except IntegrityError as err:
            await self.session.rollback()
            if "UNIQUE constraint" in str(err):
                raise HTTPException(409, "component already exists") from err
            raise
        await self.session.refresh(obj)
        return obj

    async def bulk_create(self, items: List[ComponentMasterCreate]) -> List[ComponentMaster]:
        objs = [ComponentMaster(**i.model_dump()) for i in items]
        self.session.add_all(objs)
        try:
            await self.session.commit()
        except IntegrityError as err:
            await self.session.rollback()
            raise HTTPException(409, "error inserting components") from err
        for obj in objs:
            await self.session.refresh(obj)
        return objs

    async def get_by_part_number(self, part_number: str) -> Optional[ComponentMaster]:
        stmt = select(ComponentMaster).where(ComponentMaster.part_number == part_number)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def search(
        self,
        category: Optional[str] = None,
        manufacturer: Optional[str] = None,
        min_power: Optional[float] = None,
        max_power: Optional[float] = None,
    ) -> List[ComponentMaster]:
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


async def get_component_db_service() -> ComponentDBService:
    async with SessionMaker() as session:
        yield ComponentDBService(session)
