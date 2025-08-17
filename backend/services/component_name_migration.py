"""Migration helpers for updating component names.

This module defines functions used to update existing component names when
the naming policy changes. The main entry point is
``update_existing_component_names``, which walks through all component
records in the database and regenerates their names using the current
policy.

Running this migration may be a time‑consuming operation on large
datasets. Administrators can invoke it via the naming policy API
(by specifying ``apply_to_existing=true``) or run the exported script
(`scripts/update_component_names.py`) as a standalone job.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.component_naming_service import ComponentNamingService


async def update_existing_component_names(session: AsyncSession) -> None:
    """Regenerate names for all components using the current naming policy.

    This function queries the ``ComponentMaster`` table for all records
    and updates each record’s ``name`` field by applying the current
    naming policy through :class:`backend.services.ComponentNamingService`.
    The function does not update the naming policy version on the
    component; it only regenerates the human‑friendly display name.

    Args:
        session: A SQLAlchemy ``AsyncSession`` bound to the application’s database.

    Raises:
        Exception: Propagates any exception encountered during the
            migration, causing the API to roll back and return an error.
    """
    try:
        from backend.models.component_master import ComponentMaster  # type: ignore
    except ImportError:
        try:
            from backend.models.component import Component as ComponentMaster  # type: ignore
        except ImportError as exc:  # pragma: no cover - unexpected failure
            raise RuntimeError(
                "Unable to import component model for name migration"
            ) from exc

    result = await session.execute(select(ComponentMaster))
    components = result.scalars().all()
    for comp in components:
        metadata = {
            "manufacturer": getattr(comp, "manufacturer", None),
            "part_number": getattr(comp, "part_number", None),
            "category": getattr(comp, "category", None),
            "series_name": getattr(comp, "series_name", None),
            "power": getattr(comp, "power", None),
            "capacity": getattr(comp, "capacity", None),
            "voltage": getattr(comp, "voltage", None),
        }
        new_name = ComponentNamingService.generate_name(metadata)
        if new_name:
            comp.name = new_name
    await session.commit()


__all__ = ["update_existing_component_names"]
