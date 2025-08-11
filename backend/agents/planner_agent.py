"""Task planner that inspects session state and requirements."""
from __future__ import annotations

from typing import Dict, List, Optional

from backend.services import odl_graph_service
from backend.services.component_db_service import ComponentDBService


class PlannerAgent:
    """Interprets user commands and emits a task plan."""

    def __init__(self) -> None:
        self.odl_graph_service = odl_graph_service
        self.component_db_service = ComponentDBService()

    async def plan(
        self, session_id: str, command: str, *, requirements: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Dynamically produce a list of tasks based on the current session state
        and user intent.  The planner examines the ODL graph for existing nodes
        (panels, inverters, mounts, cables) as well as stored user requirements.
        It will skip or add tasks accordingly.

        - gather_requirements: emitted if any required user input or required
          component is missing.
        - generate_design: emitted only if no panel/inverter combination exists.
        - generate_structural: emitted only after a preliminary design exists and
          no mounts have been added.
        - generate_wiring: emitted only after a preliminary design exists and no
          wiring has been added.
        - refine_validate: emitted as the final step after design exists.

        :param session_id: current design session identifier
        :param command: raw user command (e.g. "design 5kW system")
        :param requirements: optional mapping of required inputs
            (target_power, roof_area, budget)
        :returns: ordered list of task dicts with ids and initial statuses
        """
        cmd = command.lower().strip()
        if not cmd.startswith("design"):
            return []

        # Inspect graph for existing objects
        graph = await self.odl_graph_service.get_graph(session_id)
        has_panels = any(d.get("type") == "panel" for _, d in graph.nodes(data=True))
        has_inverters = any(
            d.get("type") == "inverter" for _, d in graph.nodes(data=True)
        )
        has_mounts = any(d.get("type") == "mount" for _, d in graph.nodes(data=True))
        has_wiring = any(
            d.get("type") in {"cable", "fuse"} for _, d in graph.nodes(data=True)
        )

        # Determine if requirements are complete
        reqs = graph.graph.get("requirements", {})
        requirements_complete = all(
            reqs.get(k) for k in ["target_power", "roof_area", "budget"]
        )

        tasks: List[Dict[str, str]] = []
        if not requirements_complete or not (
            await self.component_db_service.exists("panel")
            and await self.component_db_service.exists("inverter")
        ):
            tasks.append({"id": "gather_requirements", "status": "pending"})

        # Only generate design if we lack panels/inverters
        if not (has_panels and has_inverters):
            tasks.append({"id": "generate_design", "status": "pending"})

        # If a design exists but no mounts or wiring, emit structural/wiring tasks
        if has_panels and has_inverters:
            if not has_mounts:
                tasks.append({"id": "generate_structural", "status": "pending"})
            if not has_wiring:
                tasks.append({"id": "generate_wiring", "status": "pending"})
            # Always provide refine/validate at the end
            tasks.append({"id": "refine_validate", "status": "pending"})

        return tasks
