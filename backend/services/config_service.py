from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tenant_settings import TenantSettings


DEFAULT_TENANT_ID = "tenant_default"


class ConfigService:
    """CRUD for per-tenant settings with sensible defaults."""

    @staticmethod
    async def get_or_create(session: AsyncSession, tenant_id: Optional[str]) -> TenantSettings:
        tenant_id = tenant_id or DEFAULT_TENANT_ID
        row = await session.scalar(select(TenantSettings).where(TenantSettings.tenant_id == tenant_id))
        if row:
            return row
        row = TenantSettings(tenant_id=tenant_id)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def update(session: AsyncSession, tenant_id: str, data: dict) -> TenantSettings:
        row = await ConfigService.get_or_create(session, tenant_id)
        for k, v in data.items():
            if hasattr(row, k) and v is not None:
                setattr(row, k, v)
        await session.commit()
        await session.refresh(row)
        return row

