"""Domain agents operating on the ODL graph."""
from __future__ import annotations

from typing import Dict, List
from uuid import uuid4

from backend.services.component_db_service import ComponentDBService
from backend.services import odl_graph_service
from backend.services.learning_agent_service import LearningAgentService
from backend.services.placeholder_components import get_placeholder_service
from backend.schemas.odl import ODLNode, ODLEdge
import math
from datetime import datetime


class PVDesignAgent:
    """Agent responsible for photovoltaic system design.

    The agent operates on the ODL graph to produce a preliminary photovoltaic
    array.  It analyses component availability and design requirements and then
    returns a patch describing all nodes and edges to add to the graph plus a
    summary card.  When a target power is supplied the design is sized
    accordingly; otherwise a simple single‑panel/single‑inverter layout is
    produced as a fallback.
    """

    def __init__(self) -> None:
        self.component_db_service = ComponentDBService()
        self.odl_graph_service = odl_graph_service
        self.learning_agent = LearningAgentService()
        self.placeholder_service = get_placeholder_service()

    async def execute(self, session_id: str, tid: str, **kwargs) -> Dict:
        task = tid.lower().strip()
        if task == "gather_requirements":
            return await self._gather(session_id, **kwargs)
        if task == "generate_design":
            return await self._generate_design(session_id, **kwargs)
        if task in {"generate_structural", "generate wiring", "generate_wiring"}:
            return {
                "card": {
                    "title": "Delegated task",
                    "body": f"Task '{tid}' is handled by StructuralAgent or WiringAgent",
                },
                "patch": None,
            }
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
                actions.append({
                    "label": "Upload Datasheet", 
                    "command": "upload_datasheet", 
                    "variant": "primary",
                    "icon": "upload"
                })
            if missing_reqs:
                actions.append({
                    "label": "Enter Requirements", 
                    "command": "enter_requirements", 
                    "variant": "primary",
                    "icon": "form"
                })
            
            # Add specs showing what's missing vs available
            specs = []
            for field in ["target_power", "roof_area", "budget"]:
                if field in missing_reqs:
                    specs.append({"label": field.replace("_", " ").title(), "value": "Missing", "confidence": 0.0})
                else:
                    specs.append({"label": field.replace("_", " ").title(), "value": "Provided", "confidence": 1.0})
            
            enhanced_card = {
                "title": "Gather requirements",
                "body": " ".join(body_lines),
                "confidence": 0.0,
                "specs": specs,
                "actions": actions,
                "warnings": body_lines,
                "recommendations": ["Complete all requirements to proceed with design generation"]
            }
            
            return {
                "card": enhanced_card,
                "patch": None,
                "status": "blocked",
            }
        enhanced_card = {
            "title": "Gather requirements",
            "body": "All requirements and components are present. Ready to generate a design.",
            "confidence": 1.0,
            "specs": [
                {"label": "Target Power", "value": "Provided", "confidence": 1.0},
                {"label": "Roof Area", "value": "Provided", "confidence": 1.0},
                {"label": "Budget", "value": "Provided", "confidence": 1.0},
                {"label": "Components", "value": "Available", "confidence": 1.0}
            ],
            "actions": [
                {"label": "Generate Design", "command": "generate_design", "variant": "primary", "icon": "play"}
            ],
            "warnings": [],
            "recommendations": ["Proceed to generate preliminary design"]
        }
        
        return {
            "card": enhanced_card,
            "patch": None,
            "status": "complete",
        }

    async def _generate_design(self, session_id: str, **kwargs) -> Dict:
        """Enhanced design generation with placeholder support.
        
        This method can generate designs using either real components from the 
        database or placeholder components when real ones aren't available.
        """
        try:
            g = await self.odl_graph_service.get_graph(session_id)
            
            # Check if any design already exists (real or placeholder)
            has_panel = any(data.get("type") in ["panel", "generic_panel"] for _, data in g.nodes(data=True))
            has_inverter = any(data.get("type") in ["inverter", "generic_inverter"] for _, data in g.nodes(data=True))
            
            if has_panel and has_inverter:
                return {
                    "card": {
                        "title": "Generate design",
                        "body": "A preliminary design already exists. Proceed to refinement.",
                    },
                    "patch": None,
                    "status": "complete",
                }
            
            requirements = g.graph.get("requirements", {})
            target_power = requirements.get("target_power")
            
            # Check component availability
            panels_available = await self.component_db_service.search(category="panel")
            inverters_available = await self.component_db_service.search(category="inverter")
            
            components_available = bool(panels_available and inverters_available)
            
            # Decide whether to use real or placeholder components
            if components_available:
                return await self._generate_real_component_design(session_id, target_power, requirements, panels_available, inverters_available)
            else:
                return await self._generate_placeholder_design(session_id, target_power, requirements)
                
        except Exception as e:
            return {
                "card": {
                    "title": "Generate design",
                    "body": f"Error generating design: {str(e)}",
                },
                "patch": None,
                "status": "blocked",
            }

    async def _generate_placeholder_design(self, session_id: str, target_power: float, requirements: Dict) -> Dict:
        """Generate design using placeholder components."""
        try:
            # Get placeholder component definitions
            panel_placeholder = self.placeholder_service.get_placeholder_type("generic_panel")
            inverter_placeholder = self.placeholder_service.get_placeholder_type("generic_inverter")
            
            if not panel_placeholder or not inverter_placeholder:
                return {
                    "card": {
                        "title": "Generate design",
                        "body": "Placeholder components not available.",
                    },
                    "patch": None,
                    "status": "blocked",
                }
            
            # Calculate component counts using placeholder defaults
            default_panel_power = panel_placeholder.default_attributes["power"]
            default_inverter_capacity = inverter_placeholder.default_attributes["capacity"]
            
            if target_power and target_power > 0:
                panel_count = max(1, math.ceil(target_power / default_panel_power))
                total_panel_power = panel_count * default_panel_power
                inverter_count = max(1, math.ceil(total_panel_power / default_inverter_capacity))
            else:
                panel_count = 1
                inverter_count = 1
                total_panel_power = default_panel_power
            
            # Apply constraints from requirements
            roof_area = requirements.get("roof_area", 0)
            if roof_area > 0:
                panel_area = panel_placeholder.default_attributes.get("area", 2.0)
                max_panels = int(roof_area / panel_area)
                panel_count = min(panel_count, max_panels)
                total_panel_power = panel_count * default_panel_power
                inverter_count = max(1, math.ceil(total_panel_power / default_inverter_capacity))
            
            budget = requirements.get("budget", 0)
            if budget > 0:
                panel_price = panel_placeholder.default_attributes.get("price", 250)
                inverter_price = inverter_placeholder.default_attributes.get("price", 1000)
                
                # Simple budget allocation (70% panels, 30% inverters)
                panel_budget = budget * 0.7
                inverter_budget = budget * 0.3
                
                max_panels_budget = int(panel_budget / panel_price)
                max_inverters_budget = int(inverter_budget / inverter_price)
                
                panel_count = min(panel_count, max_panels_budget)
                inverter_count = min(inverter_count, max_inverters_budget)
            
            # Create placeholder nodes
            nodes = []
            edges = []
            
            # Create panels
            for i in range(panel_count):
                panel_node = self.placeholder_service.create_placeholder_node(
                    node_id=f"placeholder_panel_{i}",
                    component_type="generic_panel",
                    layer="single_line"
                )
                nodes.append(ODLNode(**panel_node))
            
            # Create inverters
            panels_per_inverter = max(1, panel_count // inverter_count)
            for i in range(inverter_count):
                inverter_node = self.placeholder_service.create_placeholder_node(
                    node_id=f"placeholder_inverter_{i}",
                    component_type="generic_inverter",
                    layer="single_line"
                )
                nodes.append(ODLNode(**inverter_node))
                
                # Connect panels to this inverter
                start_panel = i * panels_per_inverter
                end_panel = min((i + 1) * panels_per_inverter, panel_count)
                
                for j in range(start_panel, end_panel):
                    edge = ODLEdge(
                        source=f"placeholder_panel_{j}",
                        target=f"placeholder_inverter_{i}",
                        data={"type": "electrical"},
                        connection_type="electrical",
                        provisional=True
                    )
                    edges.append(edge)
            
            patch = {
                "add_nodes": [n.model_dump() for n in nodes],
                "add_edges": [e.model_dump() for e in edges]
            }
            
            confidence = 0.7  # Moderate confidence for placeholder design
            
            # Calculate estimated costs
            panel_price = panel_placeholder.default_attributes.get("price", 250)
            inverter_price = inverter_placeholder.default_attributes.get("price", 1000)
            estimated_cost = (panel_count * panel_price) + (inverter_count * inverter_price)
            
            # Create enhanced design card
            specs = [
                {"label": "Array Size", "value": f"{total_panel_power/1000:.1f} kW (estimated)", "confidence": confidence},
                {"label": "Panel Count", "value": f"{panel_count} (placeholder)", "confidence": confidence},
                {"label": "Inverter Count", "value": f"{inverter_count} (placeholder)", "confidence": confidence},
                {"label": "Design Type", "value": "Placeholder", "confidence": 1.0},
                {"label": "Estimated Cost", "value": f"${estimated_cost:,.0f}", "confidence": 0.6}
            ]
            
            actions = [
                {"label": "Accept Placeholder Design", "command": "accept_placeholder_design", "variant": "primary", "icon": "check"},
                {"label": "Upload Real Components", "command": "upload_components", "variant": "secondary", "icon": "upload"},
                {"label": "Modify Requirements", "command": "edit_requirements", "variant": "secondary", "icon": "edit"}
            ]
            
            warnings = ["Design uses placeholder components - upload datasheets to select real parts"]
            recommendations = ["Upload panel and inverter datasheets to generate realistic design"]
            
            if roof_area > 0:
                area_utilization = (panel_count * panel_placeholder.default_attributes.get("area", 2.0)) / roof_area
                if area_utilization > 0.8:
                    warnings.append(f"High roof area utilization ({area_utilization:.1%})")
            
            enhanced_card = {
                "title": "Generate placeholder design",
                "body": f"Generated placeholder design with {panel_count} generic panels and {inverter_count} generic inverters",
                "confidence": confidence,
                "specs": specs,
                "actions": actions,
                "warnings": warnings,
                "recommendations": recommendations
            }
            
            return {
                "card": enhanced_card,
                "patch": patch,
                "status": "complete"
            }
            
        except Exception as e:
            return {
                "card": {
                    "title": "Generate placeholder design",
                    "body": f"Error generating placeholder design: {str(e)}",
                },
                "patch": None,
                "status": "blocked",
            }

    async def _generate_real_component_design(self, session_id: str, target_power: float, requirements: Dict, panels: List, inverters: List) -> Dict:
        """Generate design using real components from the database."""
        try:
            # Select optimal components
            chosen_panel = max(
                panels, key=lambda p: (p.get("power", 0) / max(p.get("price", 1.0), 0.01))
            )
            
            nodes = []
            edges = []
            
            if not target_power or target_power <= 0:
                # Single panel/inverter fallback
                chosen_inverter = max(
                    inverters,
                    key=lambda inv: (inv.get("capacity", 0) / max(inv.get("price", 1.0), 0.01)),
                )
                
                panel_id = chosen_panel["part_number"]
                inverter_id = chosen_inverter["part_number"]
                
                nodes.extend([
                    ODLNode(
                        id=panel_id,
                        type="panel",
                        data={
                            "part_number": chosen_panel["part_number"],
                            "power": chosen_panel["power"],
                            "layer": "single_line",
                        }
                    ),
                    ODLNode(
                        id=inverter_id,
                        type="inverter",
                        data={
                            "part_number": chosen_inverter["part_number"],
                            "capacity": chosen_inverter["capacity"],
                            "layer": "single_line",
                        }
                    )
                ])
                
                edges.append(ODLEdge(
                    source=panel_id,
                    target=inverter_id,
                    data={"type": "electrical"},
                    connection_type="electrical"
                ))
                
                description = "Generated single-panel design"
                total_panel_power = chosen_panel["power"]
                num_panels = 1
                chosen_inverters = [chosen_inverter]
                
            else:
                # Multi-panel sized design
                panel_power = chosen_panel["power"]
                num_panels = math.ceil(target_power / panel_power)
                total_panel_power = num_panels * panel_power
                
                # Select inverters to handle total capacity
                sorted_inverters = sorted(inverters, key=lambda inv: inv.get("capacity", 0))
                remaining_power = total_panel_power
                chosen_inverters = []
                
                for inv in sorted_inverters:
                    if remaining_power <= 0:
                        break
                    chosen_inverters.append(inv)
                    remaining_power -= inv.get("capacity", 0)
                
                # Create panel nodes
                for i in range(num_panels):
                    panel_id = f"{chosen_panel['part_number']}_{i}"
                    nodes.append(ODLNode(
                        id=panel_id,
                        type="panel",
                        data={
                            "part_number": chosen_panel["part_number"],
                            "power": chosen_panel["power"],
                            "layer": "single_line",
                        }
                    ))
                
                # Create inverter nodes and connections
                for j, inv in enumerate(chosen_inverters):
                    inv_id = f"{inv['part_number']}_{uuid4().hex[:4]}"
                    nodes.append(ODLNode(
                        id=inv_id,
                        type="inverter",
                        data={
                            "part_number": inv["part_number"],
                            "capacity": inv["capacity"],
                            "layer": "single_line",
                        }
                    ))
                    
                    # Connect panels to this inverter (simple distribution)
                    panels_per_inverter = max(1, num_panels // len(chosen_inverters))
                    start_panel = j * panels_per_inverter
                    end_panel = min((j + 1) * panels_per_inverter, num_panels)
                    
                    for k in range(start_panel, end_panel):
                        panel_id = f"{chosen_panel['part_number']}_{k}"
                        edges.append(ODLEdge(
                            source=panel_id,
                            target=inv_id,
                            data={"type": "electrical"},
                            connection_type="electrical"
                        ))
                
                description = f"Generated design with {num_panels} panels and {len(chosen_inverters)} inverters"
            
            patch = {
                "add_nodes": [n.model_dump() for n in nodes],
                "add_edges": [e.model_dump() for e in edges]
            }
            
            # Score confidence
            confidence = 0.8 if target_power else 0.6
            if self.learning_agent:
                try:
                    confidence = await self.learning_agent.score_action(description)
                except Exception:
                    pass
            
            # Calculate costs
            total_cost = (num_panels * chosen_panel.get("price", 250)) + sum(inv.get("price", 1000) for inv in chosen_inverters)
            
            # Create enhanced design card
            specs = [
                {"label": "Array Size", "value": f"{total_panel_power/1000:.1f} kW", "confidence": confidence},
                {"label": "Panel Count", "value": str(num_panels), "confidence": confidence},
                {"label": "Inverter Count", "value": str(len(chosen_inverters)), "confidence": confidence},
                {"label": "Total Cost", "value": f"${total_cost:,.0f}", "confidence": 0.8}
            ]
            
            actions = [
                {"label": "Accept Design", "command": "accept_design", "variant": "primary", "icon": "check"},
                {"label": "See Alternatives", "command": "generate_alternatives", "variant": "secondary", "icon": "refresh"},
                {"label": "Modify Requirements", "command": "edit_requirements", "variant": "secondary", "icon": "edit"}
            ]
            
            warnings = []
            recommendations = []
            
            # Add warnings based on design analysis
            if target_power and abs(total_panel_power - target_power) / target_power > 0.1:
                warnings.append(f"Array output ({total_panel_power/1000:.1f} kW) differs from target ({target_power/1000:.1f} kW)")
            
            if confidence < 0.7:
                warnings.append("Low confidence design - consider reviewing requirements")
            
            # Add recommendations
            if not target_power:
                recommendations.append("Consider specifying target power for optimized sizing")
            
            if num_panels > 20:
                recommendations.append("Large array - consider structural load analysis")
            
            enhanced_card = {
                "title": "Generate design",
                "body": f"Generated {description.lower()} using real components",
                "confidence": confidence,
                "specs": specs,
                "actions": actions,
                "warnings": warnings,
                "recommendations": recommendations
            }
            
            return {
                "card": enhanced_card,
                "patch": patch,
                "status": "complete",
            }
            
        except Exception as e:
            return {
                "card": {
                    "title": "Generate design",
                    "body": f"Error generating real component design: {str(e)}",
                },
                "patch": None,
                "status": "blocked",
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
        body += " Structural and wiring tasks run separately."
        return {
            "card": {"title": "Refine/Validate", "body": body},
            "patch": None,
            "status": "complete",
        }
