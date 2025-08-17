"""Pydantic models for the naming policy API.

This module defines the request and response schemas for the naming policy
management endpoints. Administrators can fetch the current naming policy
and update it via a RESTful interface without redeploying OriginFlow.

The naming policy consists of a template string and a version number.
Changing the version allows deployments to track naming convention changes
over time. See :mod:`backend/services/component_naming_policy` for
retrieving the active policy and :mod:`backend/services/component_naming_service`
for applying the template to component metadata.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class NamingPolicy(BaseModel):
    """Response schema for the naming policy.

    Fields:
        template (str): The format string used to construct component names.
        version (int): The current naming policy version.
    """

    template: str = Field(..., description="Format string for component names")
    version: int = Field(..., description="Version of the naming policy")


class NamingPolicyUpdate(BaseModel):
    """Request schema for updating the naming policy.

    Fields:
        template (str): The new format string to apply when naming components.
        version (int): The new version number for the naming policy.
        apply_to_existing (bool): If true, all existing component names are
            regenerated using the new template. This may be a long-running
            operation depending on the number of components. See
            ``backend/services/component_name_migration.update_existing_component_names``
            for details.
    """

    template: str = Field(..., description="New template for component names")
    version: int = Field(..., description="New version for the naming policy")
    apply_to_existing: bool = Field(
        False,
        description=(
            "Whether to reapply the new naming policy to all existing components"
        ),
    )


__all__ = ["NamingPolicy", "NamingPolicyUpdate"]
