"""Agent that validates cross-layer connectivity and dependencies.

This agent analyses a design snapshot to verify that all components are
properly connected and that no elements have been left isolated.  It is
invoked via a natural-language command such as ``"validate connections"``
or ``"validate design"``.  The agent parses the `snapshot` passed in
``kwargs``, counts the number of connections for each component, and
reports components that lack any incoming or outgoing links.

Future versions of this agent may include more sophisticated checks,
such as ensuring that required sub-assemblies are present (e.g. rails
and brackets for panels) and validating cross-layer compatibility.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register, register_spec
from backend.schemas.ai import AiAction, AiActionType


class CrossLayerValidationAgent(AgentBase):
    """Validate cross-layer connections and dependencies."""

    name = "cross_layer_validation_agent"
    description = "Checks that all components have cross-layer connections."

    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
        """Inspect the snapshot and report connectivity issues.

        When the command contains the word ``validate`` and refers to ``connections`` or
        ``design``, the agent will parse the ``snapshot`` dictionary (if supplied)
        into a ``DesignSnapshot``, count the number of links per component and return
        a validation action summarising any unconnected components.  If no snapshot is
        provided, a descriptive message is returned.
        """
        # Only respond to validation commands.
        if not re.search(r"validate (connections?|design)", command, re.IGNORECASE):
            return []

        from backend.schemas.analysis import DesignSnapshot  # local import avoids circular reference

        snapshot_dict = kwargs.get("snapshot")
        if not snapshot_dict:
            # Without a snapshot we cannot inspect connectivity; ask user to provide one.
            return [
                AiAction(
                    action=AiActionType.validation,
                    payload={
                        "summary": "Unable to validate connections without a design snapshot.",
                        "issues": [],
                    },
                    version=1,
                ).model_dump()
            ]
        try:
            snapshot = DesignSnapshot.model_validate(snapshot_dict)
        except Exception:
            return [
                AiAction(
                    action=AiActionType.validation,
                    payload={
                        "summary": "Design snapshot could not be parsed.",
                        "issues": [],
                    },
                    version=1,
                ).model_dump()
            ]

        # Build connection count for each component.
        connection_count: Dict[str, int] = {c.id: 0 for c in snapshot.components}
        for link in snapshot.links:
            if link.source_id in connection_count:
                connection_count[link.source_id] += 1
            if link.target_id in connection_count:
                connection_count[link.target_id] += 1

        issues: List[str] = []
        for comp in snapshot.components:
            if connection_count.get(comp.id, 0) == 0:
                issues.append(
                    f"Component '{comp.name}' (ID: {comp.id}, Type: {comp.type}) has no connections."
                )

        summary = (
            f"Found {len(issues)} issue(s) in cross-layer validation." if issues else "All components are connected."
        )
        payload = {"summary": summary, "issues": issues}
        return [
            AiAction(
                action=AiActionType.validation,
                payload=payload,
                version=1,
            ).model_dump()
        ]


cross_layer_validation_agent = register(CrossLayerValidationAgent())
register_spec(name="cross_layer_validation_agent", domain="design")

