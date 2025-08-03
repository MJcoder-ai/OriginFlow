"""Agent that validates cross-layer connectivity and dependencies.

This agent performs a high-level check to ensure that all ports on a
component are connected and that required sub-components are present on
the appropriate layers.  It is invoked via a natural-language command
such as ``"validate connections"`` or ``"validate design connections"``.

Currently the implementation is a stub: it does not parse the
serialized snapshot provided by the AnalyzeOrchestrator.  Instead it
returns a message directing the user to perform a manual review.  In a
future release this agent will parse the design snapshot, inspect
component port definitions and dependencies, and return actionable
validation messages highlighting missing links and sub-assemblies.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiAction, AiActionType


@register
class CrossLayerValidationAgent(AgentBase):
    """Validate cross-layer connections and dependencies (stub)."""

    name = "cross_layer_validation_agent"
    description = "Checks that all ports are connected and required sub-components are present (stub)."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        # Check if the command mentions validation of connections/design
        if not re.search(r"validate (connections?|design)", command, re.IGNORECASE):
            return []
        message = (
            "Cross-layer validation is not fully implemented yet. Please manually verify that all ports are "
            "connected and that required sub-components (brackets, rails, combiner boxes, etc.) are present "
            "on the appropriate layers. Future versions of OriginFlow will analyse the design snapshot to "
            "highlight missing connections and incomplete assemblies."
        )
        return [
            AiAction(
                action=AiActionType.validation,
                payload={"message": message},
                version=1,
            ).model_dump()
        ]

