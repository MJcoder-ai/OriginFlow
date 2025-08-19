from __future__ import annotations
import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

# Optional import: if tenant settings exist, we read from there.
def _get_tenant_setting_sync():
    try:
        from backend.services.tenant_settings_service import TenantSettingsService  # noqa: F401
        return TenantSettingsService
    except Exception:
        return None


async def is_enabled(name: str, *, tenant_id: Optional[str], session: Optional[AsyncSession]) -> bool:
    """Return True if the feature flag ``name`` is enabled for the tenant.

    Resolution order:
      1. Tenant setting via ``TenantSettingsService`` (if available): key=name (boolean)
      2. Environment variable fallback: NAME in {1|true|yes|on}
      3. Default: False
    """
    svc = _get_tenant_setting_sync()
    if svc and session and tenant_id:
        try:
            val = await svc.get_bool(session, tenant_id=tenant_id, key=name)
            if val is not None:
                return bool(val)
        except Exception:
            pass

    env_key = name.upper().replace(".", "_")
    raw = os.getenv(env_key, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}
