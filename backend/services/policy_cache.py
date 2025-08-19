from __future__ import annotations
import time
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.tenant_settings_service import TenantSettingsService
from backend.observability.metrics import (
    now,
    policy_cache_get_latency,
    policy_cache_hits,
    policy_cache_misses,
    policy_cache_sets,
    policy_cache_invalidations,
)


class PolicyCache:
    """Simple in-memory cache for tenant policy documents."""

    _cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
    ttl: int = 60

    @classmethod
    async def get(cls, session: AsyncSession, tenant_id: str) -> Dict[str, Any]:
        t0 = now()
        cur = time.time()
        entry = cls._cache.get(tenant_id)
        if entry and cur - entry[0] < cls.ttl:
            try:
                policy_cache_hits.labels("memory", tenant_id).inc()
                policy_cache_get_latency.labels("memory", tenant_id).observe(now() - t0)
            except Exception:
                pass
            return entry[1]

        try:
            policy_cache_misses.labels("memory", tenant_id).inc()
        except Exception:
            pass

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
        cls._cache[tenant_id] = (cur, policy)
        try:
            policy_cache_sets.labels("memory", tenant_id).inc()
            policy_cache_get_latency.labels("db", tenant_id).observe(now() - t0)
        except Exception:
            pass
        return policy

    @classmethod
    def invalidate(cls, tenant_id: Optional[str] = None) -> None:
        if tenant_id:
            cls._cache.pop(tenant_id, None)
            try:
                policy_cache_invalidations.labels(tenant_id).inc()
            except Exception:
                pass
        else:
            cls._cache.clear()
