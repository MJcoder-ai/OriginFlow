from __future__ import annotations

import os
from typing import Optional, Tuple

from backend.utils.feature_flags import is_enabled

DEFAULT_THRESHOLD = 0.85  # fallback if no tenant setting


class ApprovalPolicyService:
    """
    Tenant-scoped approval policy.
    Sources:
      - TenantSettingsService (if present) keys:
           approvals.threshold (float 0..1)
           approvals.allowlist (list of action_type strings)
           approvals.denylist (list of action_type strings)
      - ENV fallbacks:
           APPROVALS_THRESHOLD, APPROVALS_ALLOWLIST, APPROVALS_DENYLIST
    """

    @staticmethod
    async def _get_threshold(tenant_id: str, session=None) -> float:
        # Prefer tenant settings if available
        try:
            from backend.services.tenant_settings_service import TenantSettingsService  # type: ignore

            val = await TenantSettingsService.get_float(session, tenant_id, "approvals.threshold")
            if val is not None:
                return float(val)
        except Exception:
            pass
        raw = os.getenv("APPROVALS_THRESHOLD")
        return float(raw) if raw else DEFAULT_THRESHOLD

    @staticmethod
    async def _get_list(tenant_id: str, key: str, env_key: str, session=None) -> list[str]:
        try:
            from backend.services.tenant_settings_service import TenantSettingsService  # type: ignore

            arr = await TenantSettingsService.get_list(session, tenant_id, key)
            if arr:
                return [str(x) for x in arr]
        except Exception:
            pass
        raw = os.getenv(env_key, "")
        return [x.strip() for x in raw.split(",") if x.strip()]

    @staticmethod
    async def evaluate(
        *,
        tenant_id: str,
        action_type: str,
        confidence: Optional[float],
        session=None,
    ) -> Tuple[bool, str]:
        """
        Returns (auto_approve: bool, reason: str)
        Rules:
          - If action_type in denylist -> False
          - If action_type in allowlist -> True
          - Else compare confidence against threshold
        """

        deny = await ApprovalPolicyService._get_list(
            tenant_id, "approvals.denylist", "APPROVALS_DENYLIST", session
        )
        if action_type in deny:
            return False, f"Denied by policy denylist: {action_type}"

        allow = await ApprovalPolicyService._get_list(
            tenant_id, "approvals.allowlist", "APPROVALS_ALLOWLIST", session
        )
        if action_type in allow:
            return True, f"Allowed by policy allowlist: {action_type}"

        threshold = await ApprovalPolicyService._get_threshold(tenant_id, session)
        if confidence is None:
            return False, "No confidence score; manual approval required"
        return (confidence >= threshold, f"Confidence {confidence:.2f} vs threshold {threshold:.2f}")

