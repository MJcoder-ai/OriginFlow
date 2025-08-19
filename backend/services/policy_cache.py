from __future__ import annotations
import time
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.tenant_settings_service import TenantSettingsService


class PolicyCache:
    """Simple in-memory cache for tenant policy documents."""

    _cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
    ttl: int = 60

    @classmethod
    async def get(cls, session: AsyncSession, tenant_id: str) -> Dict[str, Any]:
        now = time.time()
        entry = cls._cache.get(tenant_id)
        if entry and now - entry[0] < cls.ttl:
            return entry[1]
        ts = await TenantSettingsService.get_or_create(session, tenant_id)
        policy = {
            "auto_approve_enabled": bool(ts.auto_approve_enabled),
            "risk_threshold_default": float(ts.risk_threshold_default),
            "action_whitelist": ts.action_whitelist or {"actions": []},
            "action_blacklist": ts.action_blacklist or {"actions": []},
            "enabled_domains": ts.enabled_domains or {"domains": []},
            "feature_flags": ts.feature_flags or {},
            "data": ts.data or {},
        }
        cls._cache[tenant_id] = (now, policy)
        return policy

    @classmethod
    def invalidate(cls, tenant_id: Optional[str] = None) -> None:
        if tenant_id:
            cls._cache.pop(tenant_id, None)
        else:
            cls._cache.clear()
