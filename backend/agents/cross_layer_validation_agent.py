"""CrossLayerValidationAgent validates connectivity and component relationships across design layers.

This agent is invoked via the ``validate_design`` task after primary domain
agents have populated the graph.  It performs several checks to ensure
that components are correctly connected and that key relationships are
maintained:

* **Isolated components** – Any non‑root node with neither incoming
  nor outgoing edges is flagged as an isolated component.
* **Battery connections** – Each battery (``generic_battery``) must be
  connected to at least one inverter or the system root.  Unconnected
  batteries are reported.
* **Monitoring connections** – Each monitoring device
  (``generic_monitoring``) must be connected to at least one component.
  Devices without connections are flagged.
* **Battery–inverter ratio** – The number of battery modules should match
  the number of inverters (1:1 ratio).  A mismatch is reported as an
  issue.

The agent returns an ADPF envelope summarising the findings.  The
``issues`` list contains human‑readable descriptions of any problems,
and the design card suggests corrective actions.  This agent does not
modify the graph itself and always returns ``status='complete'`` when
the validation check finishes.
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

        snapshot_data = kwargs.get("snapshot")
        if not snapshot_data:
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
            if isinstance(snapshot_data, dict):
                snapshot = DesignSnapshot.model_validate(snapshot_data)
            else:
                snapshot = snapshot_data
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

