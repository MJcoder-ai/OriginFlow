from __future__ import annotations
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tenant_settings import TenantSettings
from backend.schemas.tenant_policy import PolicyUpdate


class TenantSettingsService:
    @staticmethod
    async def get_or_create(session: AsyncSession, tenant_id: str) -> TenantSettings:
        ts = await session.scalar(select(TenantSettings).where(TenantSettings.tenant_id == tenant_id))
        if ts:
            return ts
        ts = TenantSettings(
            tenant_id=tenant_id,
            auto_approve_enabled=True,
            risk_threshold_default=0.80,
            action_whitelist={"actions": []},
            action_blacklist={"actions": []},
            enabled_domains={"domains": []},
            feature_flags={},
            data={},
            version=1,
        )
        session.add(ts)
        await session.flush()
        return ts

    @staticmethod
    async def update(session: AsyncSession, tenant_id: str, body: PolicyUpdate, updated_by_id: str | None) -> TenantSettings:
        ts = await TenantSettingsService.get_or_create(session, tenant_id)
        if int(body.version) != int(ts.version or 1):
            raise ValueError(
                f"Version conflict. Current version is {ts.version}, provided {body.version}. Refresh and retry."
            )
        if body.auto_approve_enabled is not None:
            ts.auto_approve_enabled = body.auto_approve_enabled
        if body.risk_threshold_default is not None:
            ts.risk_threshold_default = body.risk_threshold_default
        if body.action_whitelist is not None:
            ts.action_whitelist = body.action_whitelist
        if body.action_blacklist is not None:
            ts.action_blacklist = body.action_blacklist
        if body.enabled_domains is not None:
            ts.enabled_domains = body.enabled_domains
        if body.feature_flags is not None:
            ts.feature_flags = body.feature_flags
        if body.data is not None:
            ts.data = body.data
        ts.version = int(ts.version or 1) + 1
        ts.updated_by_id = updated_by_id
        ts.updated_at = datetime.utcnow()
        await session.flush()
        try:
            from backend.services.audit_log_service import AuditLogService  # type: ignore

            await AuditLogService.record_event(
                session=session,
                tenant_id=tenant_id,
                actor_id=updated_by_id,
                event_type="tenant.settings.updated",
                payload={"tenant_id": tenant_id, "new_version": ts.version},
            )
        except Exception:
            pass
        return ts

    # ------- Helper getters used by other modules -------
    @staticmethod
    async def get_bool(session: AsyncSession, tenant_id: str, key: str) -> Optional[bool]:
        ts = await TenantSettingsService.get_or_create(session, tenant_id)
        if key in (ts.feature_flags or {}):
            return bool((ts.feature_flags or {}).get(key))
        return (ts.data or {}).get(key)

    @staticmethod
    async def get_float(session: AsyncSession, tenant_id: str, key: str) -> Optional[float]:
        ts = await TenantSettingsService.get_or_create(session, tenant_id)
        if key == "approvals.threshold":
            return float(ts.risk_threshold_default)
        return (ts.data or {}).get(key)

    @staticmethod
    async def get_list(session: AsyncSession, tenant_id: str, key: str) -> Optional[List[str]]:
        ts = await TenantSettingsService.get_or_create(session, tenant_id)
        if key == "approvals.whitelist":
            return (ts.action_whitelist or {}).get("actions", [])
        if key == "approvals.blacklist":
            return (ts.action_blacklist or {}).get("actions", [])
        val = (ts.data or {}).get(key)
        if isinstance(val, list):
            return val
        return None
