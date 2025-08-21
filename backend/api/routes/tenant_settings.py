from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.database.session import get_session
from backend.auth.dependencies import require_permission
from backend.schemas.tenant_policy import (
    PolicyDoc,
    PolicyUpdate,
    PolicyTestRequest,
    PolicyTestResult,
)
from backend.services.tenant_settings_service import TenantSettingsService

try:
    from backend.services.approval_policy_service import ApprovalPolicyService
except Exception:  # pragma: no cover - optional dependency
    ApprovalPolicyService = None  # type: ignore

router = APIRouter(prefix="/api/v1/tenant/settings", tags=["Tenant Settings"])


@router.get("", dependencies=[Depends(require_permission("tenant.settings.read"))])
async def get_policy(
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None) or "default"
    ts = await TenantSettingsService.get_or_create(session, tenant_id)
    return ts.to_dict()


@router.put("", dependencies=[Depends(require_permission("tenant.settings.write"))])
async def update_policy(
    body: PolicyUpdate,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None) or "default"
    try:
        ts = await TenantSettingsService.update(
            session, tenant_id, body, updated_by_id=getattr(user, "id", None)
        )
        await session.commit()
        return ts.to_dict()
    except ValueError as ve:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/test", dependencies=[Depends(require_permission("tenant.settings.read"))])
async def test_policy(
    body: PolicyTestRequest,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
) -> PolicyTestResult:
    tenant_id = getattr(user, "tenant_id", None) or "default"
    ts = await TenantSettingsService.get_or_create(session, tenant_id)
    if ApprovalPolicyService:
        try:
            auto, reason, thr, match = await ApprovalPolicyService.test_candidate(
                tenant_policy=ts.to_dict(),
                action_type=body.action_type,
                confidence=body.confidence,
                agent_name=body.agent_name,
            )
            return PolicyTestResult(
                auto_approved=auto,
                reason=reason,
                threshold_used=thr,
                matched_rule=match,
            )
        except Exception:
            pass
    wl = (ts.action_whitelist or {}).get("actions", [])
    bl = (ts.action_blacklist or {}).get("actions", [])
    thr = float(ts.risk_threshold_default or 0.80)
    if body.action_type in bl:
        return PolicyTestResult(
            auto_approved=False,
            reason="blacklist",
            threshold_used=thr,
            matched_rule="blacklist",
        )
    if body.action_type in wl:
        return PolicyTestResult(
            auto_approved=True,
            reason="whitelist",
            threshold_used=thr,
            matched_rule="whitelist",
        )
    if bool(ts.auto_approve_enabled) and body.confidence >= thr:
        return PolicyTestResult(
            auto_approved=True,
            reason="threshold",
            threshold_used=thr,
            matched_rule="threshold",
        )
    return PolicyTestResult(
        auto_approved=False,
        reason="below_threshold_or_disabled",
        threshold_used=thr,
        matched_rule=None,
    )
