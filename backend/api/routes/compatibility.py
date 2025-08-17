# backend/api/routes/compatibility.py
"""API routes for compatibility validation.

This module defines a FastAPI router that exposes an endpoint for
validating design snapshots using the :class:`CompatibilityEngine`.
It accepts a ``DesignSnapshot`` payload and returns a
``CompatibilityReport`` summarising any issues found.  At present the
compatibility engine is a stub that always reports no issues, but this
API can be integrated immediately to test the wiring and future rule
logic.

Endpoint summary:

* **POST /api/v1/ai/validate-compatibility** – Accepts a
  ``DesignSnapshot`` body and returns a ``CompatibilityReport``.

To enable this route, import the router from
``backend.api.routes.compatibility`` and include it in the FastAPI
application using ``app.include_router``.
"""

from fastapi import APIRouter

from backend.schemas.analysis import DesignSnapshot
from backend.services.compatibility import CompatibilityEngine, CompatibilityReport


router = APIRouter()

_engine = CompatibilityEngine()


@router.post(
    "/ai/validate-compatibility",
    response_model=CompatibilityReport,
    summary="Validate system compatibility",
    description=(
        "Validate a design snapshot across electrical, mechanical, thermal "
        "and communication compatibility rules.  Returns a report listing "
        "issues for each rule category.  Currently a stub that always "
        "returns an empty report."
    ),
)
async def validate_compatibility(snapshot: DesignSnapshot) -> CompatibilityReport:
    """Validate a design snapshot for inter-component compatibility.

    Args:
        snapshot: The design snapshot to validate.

    Returns:
        A :class:`CompatibilityReport` with validation results.
    """

    return await _engine.validate_system_compatibility(snapshot)

