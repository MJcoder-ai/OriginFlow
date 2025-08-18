from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.database.session import SessionMaker
from backend.schemas.governance import (
    TenantSettingsRead,
    TenantSettingsUpdate,
    PendingActionRead,
    PendingActionDecision,
)
from backend.services.config_service import ConfigService
from backend.services.approval_service import ApprovalService
from backend.auth.dependencies import get_current_user
from backend.auth.schemas import UserRead


router = APIRouter(prefix="/api/v1", tags=["Governance & Approvals"])


@router.get("/tenant/{tenant_id}/settings", response_model=TenantSettingsRead)
async def get_settings(tenant_id: str, user: UserRead = Depends(get_current_user)):
    async with SessionMaker() as sess:
        row = await ConfigService.get_or_create(sess, tenant_id)
        return row


@router.put("/tenant/{tenant_id}/settings", response_model=TenantSettingsRead)
async def update_settings(
    tenant_id: str,
    body: TenantSettingsUpdate,
    user: UserRead = Depends(get_current_user),
):
    if "policy:edit" not in (user.permissions or []):
        raise HTTPException(status_code=403, detail="Missing permission: policy:edit")
    async with SessionMaker() as sess:
        row = await ConfigService.update(sess, tenant_id, body.model_dump(exclude_none=True))
        return row


@router.get("/tenant/{tenant_id}/approvals", response_model=list[PendingActionRead])
async def list_pending(
    tenant_id: str,
    status: Optional[str] = Query(None, pattern="^(pending|approved|rejected)$"),
    project_id: Optional[str] = None,
    user: UserRead = Depends(get_current_user),
):
    if "approvals:review" not in (user.permissions or []):
        raise HTTPException(status_code=403, detail="Missing permission: approvals:review")
    async with SessionMaker() as sess:
        items = await ApprovalService.list(sess, tenant_id=tenant_id, status=status, project_id=project_id)
        return items


@router.post("/approvals/{pending_id}/approve", response_model=PendingActionRead)
async def approve(
    pending_id: int,
    body: PendingActionDecision,
    user: UserRead = Depends(get_current_user),
):
    if "approvals:review" not in (user.permissions or []):
        raise HTTPException(status_code=403, detail="Missing permission: approvals:review")
    async with SessionMaker() as sess:
        row = await ApprovalService.decide(
            sess,
            pending_id=pending_id,
            approved=True,
            decided_by=user.email,
            reason=body.reason,
        )
        return row


@router.post("/approvals/{pending_id}/reject", response_model=PendingActionRead)
async def reject(
    pending_id: int,
    body: PendingActionDecision,
    user: UserRead = Depends(get_current_user),
):
    if "approvals:review" not in (user.permissions or []):
        raise HTTPException(status_code=403, detail="Missing permission: approvals:review")
    async with SessionMaker() as sess:
        row = await ApprovalService.decide(
            sess,
            pending_id=pending_id,
            approved=False,
            decided_by=user.email,
            reason=body.reason,
        )
        return row

