"""Task planner that inspects session state and requirements."""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.services import odl_graph_service
from backend.services.component_db_service import ComponentDBService

# Human-readable titles for plan tasks.  Defaults to a prettified version of the
# task id when a mapping is not provided.
TASK_TITLES: Dict[str, str] = {
    "gather_requirements": "Gather requirements",
    "generate_design": "Generate design",
    "generate_structural": "Generate structural design",
    "generate_wiring": "Generate wiring",
    "refine_validate": "Refine and validate",
}


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

        When requirements are complete, the planner also records estimated
        panel and inverter counts on the graph. These estimates respect the
        user’s target power, available roof area and budget using conservative
        default component specifications when necessary.

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

        # Estimate component counts when we have requirements.  The values are
        # stored back onto the graph so downstream agents can rely on them.  Any
        # missing component attributes fall back to conservative defaults.
        if requirements_complete:
            import math

            panels = await self.component_db_service.search("panel")
            inverters = await self.component_db_service.search("inverter")
            panel_info = panels[0] if panels else {}
            inverter_info = inverters[0] if inverters else {}

            panel_power = panel_info.get("power", 400) or 400
            panel_area = panel_info.get("area", 2.0) or 2.0
            panel_price = panel_info.get("price", 250.0) or 250.0
            inverter_capacity = inverter_info.get("capacity", 5000) or 5000
            inverter_price = inverter_info.get("price", 1000.0) or 1000.0

            target_power = reqs.get("target_power", 0)
            roof_area = reqs.get("roof_area")
            budget = reqs.get("budget")

            panels_needed = max(1, math.ceil(target_power / panel_power))
            if roof_area:
                panels_needed = min(panels_needed, int(max(roof_area / panel_area, 0)))
            if budget:
                panels_needed = min(panels_needed, int(max(budget / panel_price, 0)))

            total_panel_power = panels_needed * panel_power
            inverters_needed = max(1, math.ceil(total_panel_power / inverter_capacity))
            if budget:
                remaining_budget = budget - panels_needed * panel_price
                if remaining_budget > 0:
                    inverters_needed = min(
                        inverters_needed,
                        int(max(remaining_budget / inverter_price, 1)),
                    )

            reqs["panel_count_estimate"] = panels_needed
            reqs["inverter_count_estimate"] = inverters_needed
            graph.graph["requirements"] = reqs
            await self.odl_graph_service.save_graph(session_id, graph)

        tasks: List[Dict[str, str]] = []

        # Check which required components are available in the component DB once
        panel_available = await self.component_db_service.exists("panel")
        inverter_available = await self.component_db_service.exists("inverter")
        components_available = panel_available and inverter_available

        # Emit gather_requirements when either user inputs or component data are missing
        if not requirements_complete or not components_available:
            tasks.append({"id": "gather_requirements", "status": "pending"})

        # Only generate design if we lack panels/inverters in the graph. The task
        # remains blocked until both requirements and component datasheets exist.
        if not (has_panels and has_inverters):
            gen_status = (
                "pending" if (requirements_complete and components_available) else "blocked"
            )
            tasks.append({"id": "generate_design", "status": gen_status})

        # If a design exists but no mounts or wiring, emit structural/wiring tasks
        if has_panels and has_inverters:
            if not has_mounts:
                tasks.append({"id": "generate_structural", "status": "pending"})
            if not has_wiring:
                tasks.append({"id": "generate_wiring", "status": "pending"})
            # Always provide refine/validate at the end
            tasks.append({"id": "refine_validate", "status": "pending"})

        # Attach human-readable titles to each task.  Fallback to a prettified
        # version of the id if no explicit title is defined.
        for task in tasks:
            tid = task["id"]
            task["title"] = TASK_TITLES.get(tid, tid.replace("_", " ").title())

        return tasks
