from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.approval_policy_service import ApprovalPolicyService
from backend.utils.tenant_context import get_tenant_id


class AgentRegistry:
    """Holds agent specs filtered by tenant policy."""

    def __init__(self) -> None:
        self._agents: Dict[str, Any] = {}

    async def hydrate_from_specs(self, session: AsyncSession, specs: List[Dict[str, Any]]) -> None:
        policy = await ApprovalPolicyService.for_tenant(session, get_tenant_id())
        enabled_domains = (policy.get("enabled_domains") or {}).get("domains", []) or []
        for s in specs:
            domain = s.get("domain") or s.get("category") or "generic"
            if enabled_domains and domain not in enabled_domains:
                continue
            self._agents[s["name"]] = s

    def list(self) -> List[Dict[str, Any]]:
        return list(self._agents.values())
