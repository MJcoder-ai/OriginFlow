from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.policy_cache import PolicyCache
from backend.utils.tenant_context import get_tenant_id
from backend.observability.metrics import (
    approval_decisions,
    approval_decision_latency,
    now,
)

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
        t0 = now()
        if not policy.get("auto_approve_enabled", True):
            thr = float(policy.get("risk_threshold_default", DEFAULT_THRESHOLD))
            try:
                approval_decisions.labels(
                    "deny",
                    "below_threshold_or_disabled",
                    action_type or "-",
                    agent_name or "-",
                    get_tenant_id(),
                ).inc()
                approval_decision_latency.labels(get_tenant_id()).observe(now() - t0)
            except Exception:
                pass
            return False, "Auto-approval disabled", thr, None

        deny = set((policy.get("action_blacklist") or {}).get("actions", []))
        allow = set((policy.get("action_whitelist") or {}).get("actions", []))
        thr = float(policy.get("risk_threshold_default", DEFAULT_THRESHOLD))

        if action_type in deny:
            try:
                approval_decisions.labels("deny", "blacklist", action_type or "-", agent_name or "-", get_tenant_id()).inc()
                approval_decision_latency.labels(get_tenant_id()).observe(now() - t0)
            except Exception:
                pass
            return False, f"Denied by policy denylist: {action_type}", thr, "denylist"
        if action_type in allow:
            try:
                approval_decisions.labels("allow", "whitelist", action_type or "-", agent_name or "-", get_tenant_id()).inc()
                approval_decision_latency.labels(get_tenant_id()).observe(now() - t0)
            except Exception:
                pass
            return True, f"Allowed by policy allowlist: {action_type}", thr, "allowlist"
        if confidence is None:
            try:
                approval_decisions.labels(
                    "deny",
                    "no_confidence",
                    action_type or "-",
                    agent_name or "-",
                    get_tenant_id(),
                ).inc()
                approval_decision_latency.labels(get_tenant_id()).observe(now() - t0)
            except Exception:
                pass
            return False, "No confidence score; manual approval required", thr, None

        auto = confidence >= thr
        reason_label = "threshold" if auto else "below_threshold_or_disabled"
        try:
            approval_decisions.labels(
                "allow" if auto else "deny",
                reason_label,
                action_type or "-",
                agent_name or "-",
                get_tenant_id(),
            ).inc()
            approval_decision_latency.labels(get_tenant_id()).observe(now() - t0)
        except Exception:
            pass
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
