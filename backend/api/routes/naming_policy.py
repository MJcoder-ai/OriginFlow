"""Routes for managing the component naming policy.

The naming policy controls how OriginFlow generates human‑friendly names for
components based on datasheet metadata. Administrators can retrieve the
current policy and update it via these endpoints. Updating the policy
without changing code allows teams to experiment with different naming
conventions and evolve the user experience over time.

When the policy is updated, an optional flag permits reapplying the new
template to all existing components. This triggers a migration that
regenerates component names using :class:`backend.services.ComponentNamingService`.
If you update the policy via this API with ``apply_to_existing=True``, be
aware that the operation may take a while depending on the size of the
component library.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.schemas.naming_policy import NamingPolicy, NamingPolicyUpdate
from backend.services.component_naming_policy import get_naming_policy
from backend.services.component_name_migration import update_existing_component_names
from backend.database.session import get_session


router = APIRouter(prefix="/naming-policy", tags=["Naming Policy"])


@router.get("/", response_model=NamingPolicy)
async def get_naming_policy_endpoint() -> NamingPolicy:
    """Return the active naming policy.

    This endpoint exposes the current component name template and version.
    Clients can call this endpoint to display the naming policy in admin
    interfaces or validate that the desired template is active. The
    underlying settings are loaded from environment variables or defaults
    configured in :mod:`backend.config`.
    """
    policy = get_naming_policy()
    return NamingPolicy(template=policy["template"], version=policy["version"])


@router.put("/", response_model=NamingPolicy)
async def update_naming_policy_endpoint(
    update: NamingPolicyUpdate, session: AsyncSession = Depends(get_session)
) -> NamingPolicy:
    """Update the component naming policy.

    Administrators can change the format string and version used to construct
    component names. Optionally, the new policy can be applied to all
    existing components by setting ``apply_to_existing`` to ``true``. When
    applying to existing data, the service iterates over every component
    in the database and regenerates its name using the new policy. This
    operation may be time‑consuming on large datasets; consider running the
    migration script separately if needed.

    Args:
        update: The desired naming policy configuration.
        session: Database session dependency.

    Returns:
        The updated naming policy as stored in settings.
    """
    previous_template = settings.component_name_template
    previous_version = settings.component_naming_version
    settings.component_name_template = update.template
    settings.component_naming_version = update.version

    if update.apply_to_existing:
        try:
            await update_existing_component_names(session)
        except Exception as exc:  # pragma: no cover - simple rollback path
            settings.component_name_template = previous_template
            settings.component_naming_version = previous_version
            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to apply new naming policy to existing components: "
                    f"{exc}"
                ),
            ) from exc

    return NamingPolicy(
        template=settings.component_name_template,
        version=settings.component_naming_version,
    )
