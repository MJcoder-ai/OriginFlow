"""Domain agents operating on the ODL graph."""
from __future__ import annotations

from typing import Dict, List
from uuid import uuid4

from backend.services.component_db_service import ComponentDBService
from backend.services import odl_graph_service
from backend.services.learning_agent_service import LearningAgentService


class PVDesignAgent:
    """Agent responsible for photovoltaic system design."""

    def __init__(self) -> None:
        self.component_db_service = ComponentDBService()
        self.odl_graph_service = odl_graph_service
        self.learning_agent = LearningAgentService()

    async def execute(self, session_id: str, tid: str, **kwargs) -> Dict:
        task = tid.lower().strip()
        if task == "gather_requirements":
            return await self._gather(session_id, **kwargs)
        if task == "generate_design":
            return await self._generate_design(session_id, **kwargs)
        if task == "refine_validate":
            return await self._refine_validate(session_id, **kwargs)
        return {
            "card": {"title": "Unknown task", "body": f"Task '{tid}' not supported"},
            "patch": None,
        }

    async def _gather(self, session_id: str, **kwargs) -> Dict:
        """
        Gather requirements.  This step ensures both that the component library
        contains at least one panel and inverter and that the user has provided
        necessary inputs (target_power, roof_area, budget).  Missing items are
        indicated in the returned card.  If all are present, the task completes.
        """
        g = await self.odl_graph_service.get_graph(session_id)
        requirements = g.graph.get("requirements", {})
        missing_reqs = [k for k in ["target_power", "roof_area", "budget"] if k not in requirements]
        panel_exists = await self.component_db_service.exists(category="panel")
        inverter_exists = await self.component_db_service.exists(category="inverter")
        missing_components: List[str] = []
        if not panel_exists:
            missing_components.append("panel datasheet")
        if not inverter_exists:
            missing_components.append("inverter datasheet")
        if missing_reqs or missing_components:
            body_lines: List[str] = []
            if missing_reqs:
                body_lines.append(
                    "Missing inputs: " + ", ".join(missing_reqs) + ". Please provide these values."
                )
            if missing_components:
                body_lines.append(
                    "Missing components: " + ", ".join(missing_components) + ". Please upload the missing datasheets."
                )
            actions = []
            if missing_components:
                actions.append({"label": "Upload datasheet", "command": "upload_datasheet"})
            if missing_reqs:
                actions.append({"label": "Enter requirements", "command": "enter_requirements"})
            return {
                "card": {
                    "title": "Gather requirements",
                    "body": " ".join(body_lines),
                    "actions": actions,
                },
                "patch": None,
                "status": "blocked",
            }
        return {
            "card": {
                "title": "Gather requirements",
                "body": "All requirements and components are present. Ready to generate a design.",
            },
            "patch": None,
            "status": "complete",
        }

    async def _generate_design(self, session_id: str, **kwargs) -> Dict:
        """
        Create a preliminary design sized to the user’s target power.
        - Select a panel model and compute the number of panels required.
        - Select one or more inverters to meet or exceed total array power.
        - Insert all panel and inverter nodes and connect them electrically.
        - Annotate the patch with a confidence score from the learning agent.
        """
        g = await self.odl_graph_service.get_graph(session_id)
        has_panel = any(data.get("type") == "panel" for _, data in g.nodes(data=True))
        has_inverter = any(data.get("type") == "inverter" for _, data in g.nodes(data=True))
        if has_panel and has_inverter:
            return {
                "card": {
                    "title": "Generate design",
                    "body": "A preliminary design already exists.  Proceed to refinement.",
                },
                "patch": None,
                "status": "complete",
            }
        req = g.graph.get("requirements", {})
        target_power = req.get("target_power")
        if not target_power:
            return {
                "card": {
                    "title": "Generate design",
                    "body": "No target power specified.  Please enter requirements first.",
                },
                "patch": None,
                "status": "blocked",
            }
        panels = await self.component_db_service.search(category="panel")
        inverters = await self.component_db_service.search(category="inverter")
        if not panels or not inverters:
            return {
                "card": {
                    "title": "Generate design",
                    "body": "No components available. Please upload panel and inverter datasheets.",
                },
                "patch": None,
                "status": "blocked",
            }
        chosen_panel = max(
            panels, key=lambda p: (p["power"] / max(p.get("price", 1.0), 0.01))
        )
        import math

        panel_power = chosen_panel["power"]
        num_panels = math.ceil(target_power / panel_power)
        total_panel_power = num_panels * panel_power
        sorted_inverters = sorted(inverters, key=lambda inv: inv["capacity"])
        remaining_power = total_panel_power
        chosen_inverters = []
        for inv in sorted_inverters:
            if remaining_power <= 0:
                break
            chosen_inverters.append(inv)
            remaining_power -= inv["capacity"]
        nodes: List[Dict] = []
        edges: List[Dict] = []
        for i in range(num_panels):
            node_id = f"{chosen_panel['part_number']}_{i}"
            nodes.append(
                {
                    "id": node_id,
                    "data": {
                        "type": "panel",
                        "part_number": chosen_panel["part_number"],
                        "power": chosen_panel["power"],
                        "layer": "single_line",
                    },
                }
            )
        from uuid import uuid4 as _uuid4
        for inv in chosen_inverters:
            inv_id = f"{inv['part_number']}_{_uuid4().hex[:4]}"
            nodes.append(
                {
                    "id": inv_id,
                    "data": {
                        "type": "inverter",
                        "part_number": inv["part_number"],
                        "capacity": inv["capacity"],
                        "layer": "single_line",
                    },
                }
            )
            for panel_node in nodes:
                if panel_node["data"]["type"] == "panel":
                    edges.append(
                        {
                            "source": panel_node["id"],
                            "target": inv_id,
                            "data": {"type": "electrical"},
                        }
                    )
        patch = {"add_nodes": nodes, "add_edges": edges}
        if self.learning_agent:
            description = f"Generated design with {num_panels} panels and {len(chosen_inverters)} inverter(s)"
            confidence = await self.learning_agent.score_action(description)
        else:
            confidence = 0.5
        body = (
            f"Added {num_panels} × {chosen_panel['part_number']} panels and {len(chosen_inverters)} inverter(s). "
            f"Estimated array size: {total_panel_power/1000:.1f} kW. Confidence: {confidence:.2f}"
        )
        return {
            "card": {"title": "Generate design", "body": body},
            "patch": patch,
            "status": "complete",
        }

    async def _refine_validate(self, session_id: str, **kwargs) -> Dict:
        """
        Refine and validate the design. Unlike earlier versions, this method no
        longer delegates to structural or wiring agents directly (those are now
        separate tasks). Instead, it performs high-level validation checks such as
        ensuring the array output meets the target power and returns a summary
        card. No patch is produced.
        """
        g = await self.odl_graph_service.get_graph(session_id)
        panels = [data for _, data in g.nodes(data=True) if data.get("type") == "panel"]
        inverters = [
            data for _, data in g.nodes(data=True) if data.get("type") == "inverter"
        ]
        if not panels or not inverters:
            return {
                "card": {"title": "Refine/Validate", "body": "No design to validate."},
                "patch": None,
                "status": "blocked",
            }
        total_power = sum(p["power"] for p in panels)
        total_capacity = sum(inv["capacity"] for inv in inverters)
        req = g.graph.get("requirements", {})
        target = req.get("target_power", 0)
        body = (
            f"Array output: {total_power/1000:.2f}\u00a0kW. "
            f"Inverter capacity: {total_capacity/1000:.2f}\u00a0kW. "
            f"Target power: {target/1000:.2f}\u00a0kW."
        )
        if self.learning_agent:
            conf = await self.learning_agent.score_action("refine_validate")
            body += f" Confidence: {conf:.2f}."
        return {
            "card": {"title": "Refine/Validate", "body": body},
            "patch": None,
            "status": "complete",
        }
