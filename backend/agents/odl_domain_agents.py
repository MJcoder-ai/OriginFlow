"""Domain agents operating on the ODL graph."""
from __future__ import annotations

from typing import Dict
from uuid import uuid4

from backend.services.component_db_service import ComponentDBService
from backend.services import odl_graph_service


class PVDesignAgent:
    """Agent responsible for photovoltaic system design."""

    def __init__(self) -> None:
        self.component_db_service = ComponentDBService()
        self.odl_graph_service = odl_graph_service

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
        panel_exists = await self.component_db_service.exists(category="panel")
        inverter_exists = await self.component_db_service.exists(category="inverter")
        if not panel_exists or not inverter_exists:
            missing = []
            if not panel_exists:
                missing.append("panel datasheet")
            if not inverter_exists:
                missing.append("inverter datasheet")
            return {
                "card": {
                    "title": "Gather requirements",
                    "body": f"Missing {', '.join(missing)}. Please upload the missing datasheets.",
                    "actions": [{"label": "Upload datasheet", "command": "upload_datasheet"}],
                },
                "patch": None,
                "status": "blocked",
            }
        return {
            "card": {
                "title": "Gather requirements",
                "body": "All required components exist. You may generate a preliminary design.",
            },
            "patch": None,
            "status": "complete",
        }

    async def _generate_design(self, session_id: str, **kwargs) -> Dict:
        g = self.odl_graph_service.get_graph(session_id)
        if g is None:
            g = self.odl_graph_service.create_graph(session_id)
        has_panel = any(data.get("type") == "panel" for _, data in g.nodes(data=True))
        has_inverter = any(data.get("type") == "inverter" for _, data in g.nodes(data=True))
        if has_panel and has_inverter:
            return {
                "card": {
                    "title": "Generate design",
                    "body": "A preliminary design is already present. Try refinement or validation.",
                },
                "patch": None,
                "status": "complete",
            }
        panels = await self.component_db_service.search(category="panel")
        inverters = await self.component_db_service.search(category="inverter")
        if not panels or not inverters:
            return {
                "card": {
                    "title": "Generate design",
                    "body": "No panels or inverters found. Please upload components first.",
                },
                "patch": None,
                "status": "blocked",
            }
        selected_panel = sorted(
            panels, key=lambda p: (p.get("power", 0) / max(p.get("price", 0.01), 0.01)), reverse=True
        )[0]
        selected_inverter = sorted(
            inverters,
            key=lambda inv: (inv.get("capacity", 0) / max(inv.get("price", 0.01), 0.01)),
            reverse=True,
        )[0]
        panel_id = f"panel_{selected_panel['part_number']}"
        inverter_id = f"inverter_{selected_inverter['part_number']}"
        nodes = [
            {
                "id": panel_id,
                "data": {
                    "type": "panel",
                    "part_number": selected_panel["part_number"],
                    "power": selected_panel.get("power"),
                    "layer": "single_line",
                },
            },
            {
                "id": inverter_id,
                "data": {
                    "type": "inverter",
                    "part_number": selected_inverter["part_number"],
                    "capacity": selected_inverter.get("capacity"),
                    "layer": "single_line",
                },
            },
        ]
        edge = {
            "source": panel_id,
            "target": inverter_id,
            "data": {"type": "electrical"},
        }
        patch = {"add_nodes": nodes, "add_edges": [edge]}
        return {
            "card": {
                "title": "Generate design",
                "body": (
                    f"Selected panel {selected_panel['part_number']} ({selected_panel.get('power')} W) and inverter "
                    f"{selected_inverter['part_number']} ({selected_inverter.get('capacity')} W)."
                ),
            },
            "patch": patch,
            "status": "complete",
        }

    async def _refine_validate(self, session_id: str, **kwargs) -> Dict:
        return {
            "card": {
                "title": "Refine/Validate",
                "body": "Refinement and validation logic is not yet implemented.",
            },
            "patch": None,
            "status": "pending",
        }


class StructuralAgent:
    """Placeholder structural agent."""

    async def execute(self, session_id: str, tid: str, **kwargs) -> Dict:
        return {
            "card": {
                "title": "Structural design",
                "body": "Structural sizing not yet implemented.",
            },
            "patch": None,
            "status": "pending",
        }


class WiringAgent:
    """Placeholder wiring agent."""

    async def execute(self, session_id: str, tid: str, **kwargs) -> Dict:
        return {
            "card": {
                "title": "Wiring design",
                "body": "Wiring sizing not yet implemented.",
            },
            "patch": None,
            "status": "pending",
        }
