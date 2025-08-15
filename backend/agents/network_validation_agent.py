from __future__ import annotations

"""NetworkValidationAgent for validating network connectivity in OriginFlow.

This agent inspects the ODL graph to ensure that all critical devices
(inverters and monitoring modules) are connected to at least one
network device. To accommodate both domain-specific node types
(`network` and `monitoring`) and generic placeholder types
(`generic_network` and `generic_monitoring`), the agent searches
across both naming conventions. It then checks whether any network
devices exist in the design and whether communication links connect
inverters and monitoring devices to a network device. If issues are
found, the agent returns an ADPF-compliant envelope with
recommendations for fixing the design. No graph patch is returned
because validation agents do not modify the design.
"""

import re
from typing import Any, Dict, List, Set

from backend.agents.base import AgentBase
from backend.agents.registry import register, register_spec
from backend.schemas.ai import AiAction, AiActionType


class NetworkValidationAgent(AgentBase):
    """Validate network connectivity for inverters and monitoring devices."""

    name = "network_validation_agent"
    description = "Checks that inverters and monitoring devices connect to network devices."

    async def handle(self, command: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Inspect the snapshot and report network connectivity issues."""

        if not (re.search("validate", command, re.IGNORECASE) and re.search("network", command, re.IGNORECASE)):
            return []

        from backend.schemas.analysis import DesignSnapshot  # local import to avoid circular

        snapshot_dict = kwargs.get("snapshot")
        if not snapshot_dict:
            return [
                AiAction(
                    action=AiActionType.validation,
                    payload={
                        "summary": "Unable to validate network without a design snapshot.",
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

        network_types = {"network", "generic_network"}
        inverter_types = {"inverter", "generic_inverter"}
        monitoring_types = {"monitoring", "generic_monitoring"}

        components_by_id = {c.id: c for c in snapshot.components}
        network_nodes: Set[str] = {c.id for c in snapshot.components if c.type in network_types}
        inverter_nodes: Set[str] = {c.id for c in snapshot.components if c.type in inverter_types}
        monitoring_nodes: Set[str] = {c.id for c in snapshot.components if c.type in monitoring_types}

        # Build undirected adjacency map
        adjacency: Dict[str, Set[str]] = {c.id: set() for c in snapshot.components}
        for link in snapshot.links:
            if link.source_id in adjacency and link.target_id in adjacency:
                adjacency[link.source_id].add(link.target_id)
                adjacency[link.target_id].add(link.source_id)

        reachable: Set[str] = set()
        queue: List[str] = list(network_nodes)
        while queue:
            node = queue.pop(0)
            if node in reachable:
                continue
            reachable.add(node)
            queue.extend(n for n in adjacency.get(node, []) if n not in reachable)

        issues: List[str] = []
        if not network_nodes:
            issues.append("No network devices found in the design.")

        for inv_id in inverter_nodes:
            if inv_id not in reachable:
                comp = components_by_id[inv_id]
                issues.append(
                    f"Inverter '{comp.name}' (ID: {inv_id}) is not connected to a network device."
                )

        for mon_id in monitoring_nodes:
            if mon_id not in reachable:
                comp = components_by_id[mon_id]
                issues.append(
                    f"Monitoring device '{comp.name}' (ID: {mon_id}) is not connected to a network device."
                )

        summary = (
            f"Found {len(issues)} issue(s) in network validation."
            if issues
            else "All inverters and monitoring devices are connected to network devices."
        )
        payload = {"summary": summary, "issues": issues}

        return [
            AiAction(
                action=AiActionType.validation,
                payload=payload,
                version=1,
            ).model_dump()
        ]


network_validation_agent = register(NetworkValidationAgent())
register_spec(name="network_validation_agent", domain="network")
