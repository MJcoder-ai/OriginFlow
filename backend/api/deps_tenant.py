from __future__ import annotations
from fastapi import Depends
from backend.api.deps import get_current_user

try:
    from backend.utils.tenant_context import set_tenant_id
except Exception:  # pragma: no cover
    def set_tenant_id(_: str | None) -> None:  # fallback noop
        return

async def seed_tenant_context(user = Depends(get_current_user)):
    """FastAPI dependency to ensure TenantContext is correctly set per request."""
    tid = getattr(user, "tenant_id", None) or "default"
    set_tenant_id(tid)
    return tid
