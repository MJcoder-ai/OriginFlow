# backend/services/file_service.py
"""Business logic for file uploads."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.file_asset import FileAsset
from backend.utils.id import generate_id


class FileService:
    """Service layer for file asset CRUD."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_asset(self, data: dict) -> FileAsset:
        payload = dict(data)
        asset_id = payload.pop("id", generate_id("asset"))
        obj = FileAsset(id=asset_id, **payload)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

