from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.database.session import SessionMaker
from backend.schemas.governance import TenantSettingsRead, TenantSettingsUpdate
from backend.services.config_service import ConfigService
from backend.auth.dependencies import get_current_user
from backend.auth.schemas import UserRead


router = APIRouter(prefix="/api/v1", tags=["Governance"])


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



