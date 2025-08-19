from __future__ import annotations
import time
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.feature_flags import is_enabled
from backend.models.agent_catalog import AgentCatalog
from backend.services.agent_catalog_service import AgentCatalogService
from backend.agents import registry

AGENTS_HYDRATE_FLAG = "agents.hydrate_from_db"


class AgentHydrator:
    """Resolve per-tenant published agent specs and overlay them temporarily."""

    _cache: Dict[str, Tuple[float, List[dict]]] = {}
    _ttl_seconds: int = 60

    @staticmethod
    async def should_hydrate(session: AsyncSession, tenant_id: Optional[str]) -> bool:
        return await is_enabled(AGENTS_HYDRATE_FLAG, tenant_id=tenant_id, session=session)

    @staticmethod
    def invalidate(tenant_id: Optional[str] = None) -> None:
        if tenant_id:
            AgentHydrator._cache.pop(tenant_id, None)
        else:
            AgentHydrator._cache.clear()

    @staticmethod
    async def _load_specs_from_db(session: AsyncSession, tenant_id: str) -> List[dict]:
        specs: List[dict] = []
        rows = (await session.execute(select(AgentCatalog))).scalars().all()
        for cat in rows:
            effective, state = await AgentCatalogService.resolved_agent_for_tenant(session, tenant_id, cat.name)
            if not state or not state.enabled:
                continue
            if not effective or effective.status != "published":
                continue
            spec = dict(effective.spec)
            if state.config_override:
                spec["config"] = {**(spec.get("config") or {}), **state.config_override}
            specs.append(spec)
        return specs

    @staticmethod
    async def overlay_specs_for_tenant(session: AsyncSession, tenant_id: str) -> List[dict]:
        now = time.time()
        hit = AgentHydrator._cache.get(tenant_id)
        if hit and (now - hit[0] < AgentHydrator._ttl_seconds):
            return hit[1]
        specs = await AgentHydrator._load_specs_from_db(session, tenant_id)
        AgentHydrator._cache[tenant_id] = (now, specs)
        return specs

    @staticmethod
    @contextmanager
    def temporary_overlay(specs: List[dict]):
        token = registry._temporary_overlay_register(specs)
        try:
            yield
        finally:
            registry._temporary_overlay_reset(token)
