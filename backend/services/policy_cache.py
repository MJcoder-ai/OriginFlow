from __future__ import annotations
import asyncio
import json
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
    policy_cache_db_load_latency,
    policy_cache_dogpile_wait,
)


class PolicyCache:
    """Layered policy cache with optional Redis and metrics."""

    ttl: int = 60
    _mem: Dict[str, tuple[float, Dict[str, Any]]] = {}
    _locks: Dict[str, asyncio.Lock] = {}

    @staticmethod
    async def _redis():  # pragma: no cover - overridden in tests
        return None

    @staticmethod
    def _redis_key(tenant_id: str) -> str:
        return f"policy:{tenant_id}"

    @classmethod
    async def set(cls, tenant_id: str, policy: Dict[str, Any], ttl: Optional[int] = None) -> None:
        exp = time.time() + (ttl or cls.ttl)
        cls._mem[tenant_id] = (exp, policy)
        try:
            policy_cache_sets.labels("memory", tenant_id).inc()
        except Exception:  # pragma: no cover
            pass
        r = await cls._redis()
        if r:
            try:
                await r.setex(cls._redis_key(tenant_id), ttl or cls.ttl, json.dumps({"value": policy, "version": policy.get("version", 1)}))
                policy_cache_sets.labels("redis", tenant_id).inc()
            except Exception:  # pragma: no cover
                pass

    @classmethod
    async def get(cls, session: AsyncSession, tenant_id: str) -> Dict[str, Any]:
        t0 = now()
        cur = time.time()
        entry = cls._mem.get(tenant_id)
        if entry and cur < entry[0]:
            try:
                policy_cache_hits.labels("memory", tenant_id).inc()
                policy_cache_get_latency.labels("memory", tenant_id).observe(now() - t0)
            except Exception:  # pragma: no cover
                pass
            return entry[1]

        try:
            policy_cache_misses.labels("memory", tenant_id).inc()
        except Exception:  # pragma: no cover
            pass

        r = await cls._redis()
        if r:
            try:
                raw = await r.get(cls._redis_key(tenant_id))
            except Exception:  # pragma: no cover
                raw = None
            if raw:
                try:
                    obj = json.loads(raw)
                except Exception:  # pragma: no cover
                    obj = {"value": None}
                policy = obj.get("value")
                if policy is not None:
                    cls._mem[tenant_id] = (time.time() + cls.ttl, policy)
                    try:
                        policy_cache_hits.labels("redis", tenant_id).inc()
                        policy_cache_get_latency.labels("redis", tenant_id).observe(now() - t0)
                    except Exception:  # pragma: no cover
                        pass
                    return policy
            try:
                policy_cache_misses.labels("redis", tenant_id).inc()
            except Exception:  # pragma: no cover
                pass
        else:
            try:
                policy_cache_misses.labels("redis", tenant_id).inc()
            except Exception:  # pragma: no cover
                pass

        lock = cls._locks.setdefault(tenant_id, asyncio.Lock())
        if lock.locked():
            try:
                policy_cache_dogpile_wait.labels(tenant_id).inc()
            except Exception:  # pragma: no cover
                pass
        async with lock:
            cur = time.time()
            entry = cls._mem.get(tenant_id)
            if entry and cur < entry[0]:
                try:
                    policy_cache_hits.labels("memory", tenant_id).inc()
                    policy_cache_get_latency.labels("memory", tenant_id).observe(now() - t0)
                except Exception:  # pragma: no cover
                    pass
                return entry[1]

            db_t0 = now()
            ts = await TenantSettingsService.get_or_create(session, tenant_id)
            try:
                data = ts.to_dict()  # type: ignore[assignment]
            except Exception:
                if isinstance(ts, dict):
                    data = ts
                else:
                    data = {
                        "auto_approve_enabled": True,
                        "risk_threshold_default": 0.8,
                        "action_whitelist": {"actions": []},
                        "action_blacklist": {"actions": []},
                        "enabled_domains": {"domains": []},
                        "feature_flags": {},
                        "data": {},
                        "version": 1,
                    }
            policy = {
                "auto_approve_enabled": bool(data.get("auto_approve_enabled", True)),
                "risk_threshold_default": float(data.get("risk_threshold_default", 0.8)),
                "action_whitelist": data.get("action_whitelist") or {"actions": []},
                "action_blacklist": data.get("action_blacklist") or {"actions": []},
                "enabled_domains": data.get("enabled_domains") or {"domains": []},
                "feature_flags": data.get("feature_flags") or {},
                "data": data.get("data") or {},
                "version": int(data.get("version", 1)),
            }
            cls._mem[tenant_id] = (time.time() + cls.ttl, policy)
            try:
                policy_cache_misses.labels("db", tenant_id).inc()
                policy_cache_db_load_latency.labels(tenant_id).observe(now() - db_t0)
                policy_cache_get_latency.labels("db", tenant_id).observe(now() - t0)
                policy_cache_sets.labels("memory", tenant_id).inc()
                policy_cache_dogpile_wait.labels(tenant_id).inc()
            except Exception:  # pragma: no cover
                pass
            if r:
                try:
                    await r.setex(cls._redis_key(tenant_id), cls.ttl, json.dumps({"value": policy, "version": policy.get("version", 1)}))
                    policy_cache_sets.labels("redis", tenant_id).inc()
                except Exception:  # pragma: no cover
                    pass
            return policy

    @classmethod
    def invalidate(cls, tenant_id: Optional[str] = None) -> None:
        if tenant_id:
            cls._mem.pop(tenant_id, None)
            try:
                policy_cache_invalidations.labels(tenant_id).inc()
            except Exception:  # pragma: no cover
                pass
        else:
            cls._mem.clear()
