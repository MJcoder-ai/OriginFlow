from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.policy_cache import PolicyCache
from backend.utils.tenant_context import get_tenant_id

DEFAULT_THRESHOLD = 0.85


class ApprovalPolicyService:
    """Tenant-scoped approval policy served from ``PolicyCache``."""

    @staticmethod
    async def for_tenant(session: AsyncSession, tenant_id: str) -> Dict[str, Any]:
        return await PolicyCache.get(session, tenant_id)

    @staticmethod
    async def for_request(session: AsyncSession) -> Dict[str, Any]:
        return await PolicyCache.get(session, get_tenant_id())

    @staticmethod
    async def is_auto_approved(
        policy: Dict[str, Any],
        action_type: str,
        confidence: Optional[float],
        agent_name: Optional[str] = None,
    ) -> Tuple[bool, str, float, Optional[str]]:
        """Evaluate an action against the provided policy."""
        if not policy.get("auto_approve_enabled", True):
            thr = float(policy.get("risk_threshold_default", DEFAULT_THRESHOLD))
            return False, "Auto-approval disabled", thr, None

        deny = set((policy.get("action_blacklist") or {}).get("actions", []))
        allow = set((policy.get("action_whitelist") or {}).get("actions", []))
        thr = float(policy.get("risk_threshold_default", DEFAULT_THRESHOLD))

        if action_type in deny:
            return False, f"Denied by policy denylist: {action_type}", thr, "denylist"
        if action_type in allow:
            return True, f"Allowed by policy allowlist: {action_type}", thr, "allowlist"
        if confidence is None:
            return False, "No confidence score; manual approval required", thr, None

        auto = confidence >= thr
        return auto, f"Confidence {confidence:.2f} vs threshold {thr:.2f}", thr, None

    @staticmethod
    async def evaluate(
        *,
        tenant_id: str,
        action_type: str,
        confidence: Optional[float],
        session: AsyncSession,
    ) -> Tuple[bool, str]:
        """Backward compatible helper used in legacy code paths."""
        policy = await ApprovalPolicyService.for_tenant(session, tenant_id)
        auto, reason, _, _ = await ApprovalPolicyService.is_auto_approved(
            policy, action_type, confidence, None
        )
        return auto, reason
