"""Task planner that inspects session state and requirements."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from backend.services import odl_graph_service
from backend.services.component_db_service import ComponentDBService
from backend.services.ai_clients import get_openai_client
from backend.services.placeholder_components import get_placeholder_service
from backend.services.nlp_service import parse_command
from collections import Counter

# Human-readable titles for plan tasks.  Defaults to a prettified version of the
# task id when a mapping is not provided.
TASK_TITLES: Dict[str, str] = {
    "gather_requirements": "Gather requirements",
    "generate_design": "Generate PV design",
    "generate_structural": "Generate mounting structure",
    "generate_wiring": "Generate wiring design",
    "wiring": "Generate wiring design",
    "populate_real_components": "Select real components",
    "generate_battery": "Generate battery design",
    "generate_monitoring": "Generate monitoring design",
    "generate_network": "Generate network design",
    "generate_site": "Generate site plan",
    "refine_validate": "Refine and validate design",
}


class PlannerAgent:
    """Interprets user commands and emits a task plan."""

    def __init__(self) -> None:
        self.odl_graph_service = odl_graph_service
        self.component_db_service = ComponentDBService()
        self.openai_client = get_openai_client()
        self.placeholder_service = get_placeholder_service()

    async def plan(
        self, session_id: str, command: str, *, requirements: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Dynamically produce a list of tasks based on the current session state
        and user intent. This enhanced version performs deeper analysis of the
        graph state and requirements to emit contextually appropriate tasks.

        Task Decision Logic:
        - gather_requirements: emitted if any required user input or component datasheets are missing.
        - generate_design: emitted only if no panel/inverter combination exists AND requirements are complete
          (or placeholder components are allowed).
        - downstream domain tasks (generate_structural, generate_wiring) are always scheduled once a
          preliminary design exists to ensure mounts and wiring are generated.
        - generate_battery is scheduled only when backup_hours are provided or the planner determines a battery
          is needed (``_should_add_battery_design``), preserving the ability to design systems without storage.
        - generate_monitoring is scheduled only when target_power exceeds a threshold or the planner deems
          monitoring necessary (``_should_add_monitoring``), preserving the ability to design systems without monitoring.
        - generate_network and generate_site are not scheduled by default. These tasks
          depend on agents that are not yet registered in the backend; scheduling them
          prematurely would result in an "Unknown task" error.  Once network and site
          planning agents are implemented and registered, these tasks can be re-enabled.
        - refine_validate: always emitted as the final step to validate the entire design.

        The planner now includes:
        - Graph state inspection using describe_graph helper
        - Component availability checking
        - Dynamic task ordering based on dependencies
        - Status assignment (pending/blocked) based on prerequisites

        :param session_id: current design session identifier
        :param command: raw user command (e.g. "design 5kW system")
        :param requirements: optional mapping of required inputs
            (target_power, roof_area, budget)
        :returns: ordered list of task dicts with ids, statuses, and context
        """
        cmd = command.lower().strip()

        # Attempt to derive structured hints from the free-text command. The
        # planner tolerates parsing failures and simply proceeds without
        # additional hints if anything goes wrong.
        try:
            parsed = parse_command(command)
        except Exception:
            parsed = {}

        # Handle special commands that should continue the design workflow
        if cmd == "accept_placeholder_design":
            # User accepted placeholder design, continue with next steps
            return await self._plan_continuation_tasks(session_id)
        elif cmd in ["upload_components", "edit_requirements"]:
            # These commands should restart the design process
            return await self.plan(session_id, "design system")
        elif not cmd.startswith("design"):
            return []

        # Get current graph and analyze its state
        graph = await self.odl_graph_service.get_graph(session_id)
        if graph is None:
            # If no graph exists, create one
            graph = await self.odl_graph_service.create_graph(session_id)

        # Merge parsed hints into stored requirements, filling in values only
        # when they are currently missing or falsy.  This allows users to state
        # values directly in natural language commands like "design a 5 kW
        # system" which then inform downstream planning logic.
        if parsed:
            reqs_dict = graph.graph.get("requirements", {}) or {}
            for key, value in parsed.items():
                if key not in reqs_dict or reqs_dict.get(key) in (None, 0, ""):
                    reqs_dict[key] = value
            graph.graph["requirements"] = reqs_dict
            await self.odl_graph_service.save_graph(session_id, graph)

        # Enhanced graph state analysis with placeholder support
        state = await self._analyze_graph_state(graph)
        
        # Extract commonly used values
        has_panels = state["has_panels"]
        has_inverters = state["has_inverters"] 
        has_mounts = state["has_mounts"]
        has_wiring = state["has_wiring"]
        panel_count = state["panel_count"]
        inverter_count = state["inverter_count"]
        requirements_complete = state["requirements_complete"]
        components_available = state["components_available"]
        has_preliminary_design = state["has_preliminary_design"]
        missing_requirements = state["missing_requirements"]
        reqs = state["requirements"]

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

        # Build dynamic task list based on current state
        tasks: List[Dict[str, str]] = []

        # Phase 1: Gather Requirements (blocked if inputs/components missing for real design)
        if not requirements_complete or (not components_available and not state["allow_placeholder_design"]):
            missing_items = []
            if missing_requirements:
                missing_items.extend(missing_requirements)
            if not components_available and not state["allow_placeholder_design"]:
                if not state["panel_available"]:
                    missing_items.append("panel datasheet")
                if not state["inverter_available"]:
                    missing_items.append("inverter datasheet")

            tasks.append({
                "id": "gather_requirements",
                "status": "blocked",
                "reason": f"Missing: {', '.join(missing_items)}",
                "missing_requirements": missing_requirements,
                "missing_components": [] if components_available else ["panel", "inverter"],
                "can_use_placeholders": state["allow_placeholder_design"]
            })

        # Phase 2: Generate Design (only if no preliminary design exists)
        if not has_preliminary_design:
            if requirements_complete and (components_available or state["allow_placeholder_design"]):
                design_status = "pending"
                if components_available:
                    design_reason = "Ready to generate design with real components"
                else:
                    design_reason = "Ready to generate placeholder design"
            else:
                design_status = "blocked"
                blockers = []
                if not requirements_complete:
                    blockers.append("requirements incomplete")
                if not components_available and not state["allow_placeholder_design"]:
                    blockers.append("components unavailable")
                design_reason = f"Blocked by: {', '.join(blockers)}"
            
            tasks.append({
                "id": "generate_design",
                "status": design_status,
                "reason": design_reason,
                "estimated_panels": panel_count if panel_count > 0 else reqs.get("panel_count_estimate", 1),
                "estimated_inverters": inverter_count if inverter_count > 0 else reqs.get("inverter_count_estimate", 1),
                "design_type": "real" if components_available else "placeholder"
            })

        # NEW: Phase 2.5: Populate Real Components (only if placeholders exist and real components available)
        if state["has_placeholders"] and state["components_available"]:
            placeholder_summary = self._create_placeholder_summary(state["placeholders_by_type"])
            tasks.append({
                "id": "populate_real_components",
                "status": "pending",
                "reason": f"Replace {state['total_placeholders']} placeholder component(s)",
                "placeholder_summary": placeholder_summary,
                "estimated_selections": state["total_placeholders"],
                "available_replacements": state.get("available_replacement_count", 0)
            })

        # Phase 3+: Downstream domain tasks.  Once a preliminary design exists we always
        # schedule structural and wiring tasks.  Battery and monitoring tasks remain conditional
        # so that users can design systems without storage or monitoring.  Note: network and
        # site tasks are intentionally omitted here because they depend on agents that are not
        # yet implemented in the backend; scheduling them would cause "Unknown task" errors.
        if has_preliminary_design:
            # Structural design: always add mounts for panels.
            tasks.append({
                "id": "generate_structural",
                "status": "pending",
                "reason": f"Generate mounting for {panel_count} panel{'s' if panel_count != 1 else ''}"
            })

            # Wiring design: always add cables and protective devices.
            tasks.append({
                "id": "generate_wiring",
                "status": "pending",
                "reason": f"Generate wiring between {panel_count} panel{'s' if panel_count != 1 else ''} and {inverter_count} inverter{'s' if inverter_count != 1 else ''}"
            })

            # Battery design: schedule only if battery sizing is required.
            if self._should_add_battery_design(reqs, state):
                tasks.append({
                    "id": "generate_battery",
                    "status": "pending",
                    "reason": f"Design battery system for {reqs.get('backup_hours', 8)} hours backup",
                    "backup_hours": reqs.get('backup_hours', 8),
                    "estimated_capacity": self._estimate_battery_capacity(reqs)
                })

            # Monitoring design: schedule only if monitoring is required.
            if self._should_add_monitoring(reqs, state):
                tasks.append({
                    "id": "generate_monitoring",
                    "status": "pending",
                    "reason": "Add system monitoring and data collection",
                    "monitoring_type": "basic"
                })

            # Network and site tasks are intentionally omitted until backend support exists.

        # Phase 5: Refine and Validate (always appended)
        validation_status = "pending"
        completion_items: List[str] = []
        if has_mounts:
            completion_items.append("structural")
        if has_wiring:
            completion_items.append("wiring")
        if state.get("has_batteries", False):
            completion_items.append("battery")
        if state.get("has_monitoring", False):
            completion_items.append("monitoring")

        if has_preliminary_design:
            if completion_items:
                validation_reason = f"Validate design with {', '.join(completion_items)}"
            else:
                validation_reason = "Validate preliminary design"
            design_completeness = len(completion_items) / 4.0  # Updated for new domains
        else:
            validation_reason = "Awaiting preliminary design"
            design_completeness = 0.0

        tasks.append({
            "id": "refine_validate",
            "status": validation_status,
            "reason": validation_reason,
            "design_completeness": design_completeness,
            "placeholder_percentage": state.get("placeholder_percentage", 0.0)
        })

        # Enhance all tasks with titles and context
        for task in tasks:
            tid = task["id"]
            task["title"] = TASK_TITLES.get(tid, tid.replace("_", " ").title())
            
            # Add graph summary for context
            if "graph_summary" not in task:
                task["graph_summary"] = odl_graph_service.describe_graph(graph)

        return tasks

    async def _plan_continuation_tasks(self, session_id: str) -> List[Dict[str, str]]:
        """Plan continuation tasks after placeholder design acceptance.
        
        This method generates the next logical tasks in the design workflow
        after the user has accepted a placeholder design.
        """
        # Get current graph and analyze its state
        graph = await self.odl_graph_service.get_graph(session_id)
        if graph is None:
            return []

        # Analyze graph state to determine next steps
        state = await self._analyze_graph_state(graph)
        
        tasks: List[Dict[str, str]] = []
        
        # Mark the current design as accepted by updating provisional edges
        # This converts provisional electrical connections to confirmed ones
        patch = {"update_edges": []}
        for u, v, edge_data in graph.edges(data=True):
            if edge_data.get("provisional", False):
                patch["update_edges"].append({
                    "source": u,
                    "target": v,
                    "data": {**edge_data, "provisional": False}
                })
        
        if patch["update_edges"]:
            await self.odl_graph_service.apply_patch(session_id, patch)
        
        # Generate next logical tasks
        has_panels = state["has_panels"]
        has_inverters = state["has_inverters"]

        # Always schedule structural and wiring tasks to progress design
        if has_panels:
            tasks.append({
                "id": "generate_structural",
                "title": "Generate Structural Design",
                "status": "pending",
                "reason": "Add mounting systems for panels",
                "description": "Design and size mounting hardware for the solar array"
            })

        if has_panels or has_inverters:
            tasks.append({
                "id": "generate_wiring",
                "title": "Generate Wiring Design",
                "status": "pending",
                "reason": "Add cables and protective devices",
                "description": "Size and route electrical wiring between components"
            })

        # Add domain-specific tasks based on requirements
        requirements = graph.graph.get("requirements", {})
        if self._should_add_battery_design(requirements, state):
            tasks.append({
                "id": "generate_battery",
                "title": "Generate Battery Storage",
                "status": "pending",
                "reason": "Backup power requirement specified",
                "description": f"Add battery storage for {requirements.get('backup_hours', 8)} hours backup"
            })

        if self._should_add_monitoring(requirements, state):
            tasks.append({
                "id": "generate_monitoring",
                "title": "Generate Monitoring System",
                "status": "pending",
                "reason": "Large system requires monitoring",
                "description": "Add performance monitoring and data collection"
            })

        # Network and site tasks are intentionally omitted until backend support exists.

        # Always add refinement as final step
        tasks.append({
            "id": "refine_validate",
            "title": "Refine & Validate",
            "status": "pending",
            "reason": "Final design optimization and validation",
            "description": "Optimize design and validate all requirements"
        })

        return tasks

    async def _build_planning_context(
        self, graph, requirements: Dict, command: str, available_tools: List[str]
    ) -> str:
        """
        Build a comprehensive context prompt for LLM-based planning decisions.
        
        This method creates a rich context that includes:
        - Current graph summary with component counts and warnings
        - Requirements status and missing inputs
        - Available domain agent tools
        - User command intent
        - Suggested task sequencing based on dependencies
        
        Args:
            graph: Current ODL graph
            requirements: User requirements dictionary
            command: Original user command
            available_tools: List of available domain agent names
            
        Returns:
            Formatted context string for LLM planning
        """
        # Get comprehensive graph summary
        graph_summary = odl_graph_service.describe_graph(graph)
        
        # Format requirements status
        required_fields = ["target_power", "roof_area", "budget"]
        missing_reqs = [k for k in required_fields if not requirements.get(k)]
        reqs_status = {
            "complete": len(missing_reqs) == 0,
            "missing": missing_reqs,
            "provided": {k: v for k, v in requirements.items() if v is not None}
        }
        
        # Check component availability
        components_status = {
            "panels_available": await self.component_db_service.exists(category="panel"),
            "inverters_available": await self.component_db_service.exists(category="inverter")
        }
        
        # Build context prompt
        context = f"""Current Design Session Analysis:

GRAPH STATE: {graph_summary}

REQUIREMENTS STATUS:
- Complete: {reqs_status['complete']}
- Missing: {', '.join(missing_reqs) if missing_reqs else 'None'}
- Provided: {json.dumps(reqs_status['provided'], indent=2)}

COMPONENT AVAILABILITY:
- Panels available in library: {components_status['panels_available']}
- Inverters available in library: {components_status['inverters_available']}

AVAILABLE TOOLS: {', '.join(available_tools)}

USER COMMAND: "{command}"

        PLANNING GUIDELINES:
        - gather_requirements: Use when missing user inputs or component datasheets
        - generate_design: Use after requirements complete and components available
        - generate_structural: Use once a preliminary design exists to add mounting
        - generate_wiring: Use once a preliminary design exists to add electrical connections
        - generate_battery: Use when backup power is required or recommended
        - generate_monitoring: Use for large systems or when monitoring is needed
        - refine_validate: Use as final validation step

Task statuses should be:
- "pending": Ready to execute immediately
- "blocked": Cannot execute due to missing prerequisites
- "complete": Already finished successfully

Return a JSON array of tasks with reasoning for each decision."""

        return context

    async def _llm_enhanced_planning(
        self, session_id: str, command: str, graph, requirements: Dict
    ) -> Optional[List[Dict]]:
        """
        Use LLM to enhance planning decisions with contextual reasoning.
        
        This method supplements the rule-based planner with LLM insights for
        complex scenarios where static rules might miss important context.
        
        Args:
            session_id: Session identifier
            command: User command
            graph: Current graph state
            requirements: Requirements dictionary
            
        Returns:
            Optional list of enhanced task dictionaries, or None if LLM unavailable
        """
        try:
            # Available domain agents
            available_tools = [
                "gather_requirements", "generate_design", "generate_structural",
                "generate_wiring", "generate_battery", "generate_monitoring",
                "refine_validate"
            ]
            
            # Build rich context for LLM
            context = await self._build_planning_context(
                graph, requirements, command, available_tools
            )
            
            # Call LLM for enhanced planning insights
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI planning agent for solar PV system design. Analyze the current session state and recommend an optimal task sequence."
                    },
                    {
                        "role": "user", 
                        "content": context
                    }
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse LLM response
            llm_content = response.choices[0].message.content
            if llm_content and llm_content.strip().startswith('['):
                # Try to parse as JSON
                llm_tasks = json.loads(llm_content)
                
                # Validate and enrich LLM suggestions
                validated_tasks = []
                for task in llm_tasks:
                    if isinstance(task, dict) and "id" in task:
                        # Add standard fields if missing
                        task.setdefault("status", "pending")
                        task.setdefault("title", TASK_TITLES.get(task["id"], task["id"].replace("_", " ").title()))
                        task.setdefault("graph_summary", odl_graph_service.describe_graph(graph))
                        validated_tasks.append(task)
                
                return validated_tasks
                
        except Exception as e:
            # Fall back gracefully if LLM fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"LLM-enhanced planning failed, using rule-based fallback: {e}")
            return None
        
        return None

    async def _analyze_graph_state(self, graph) -> Dict[str, Any]:
        """Enhanced graph state analysis including placeholder detection."""
        try:
            nodes = {n: d for n, d in graph.nodes(data=True)}
            
            # Basic component analysis
            has_panels = any(d.get("type") in ["panel", "generic_panel"] for d in nodes.values())
            has_inverters = any(d.get("type") in ["inverter", "generic_inverter"] for d in nodes.values())
            has_mounts = any(d.get("type") in ["mount", "generic_mount"] for d in nodes.values())
            has_wiring = any(d.get("type") in ["cable", "fuse", "generic_cable", "generic_fuse"] for d in nodes.values())
            has_batteries = any(d.get("type") in ["battery", "generic_battery"] for d in nodes.values())
            has_monitoring = any(d.get("type") in ["monitoring", "generic_monitoring"] for d in nodes.values())
            
            # Count components
            panel_count = len([d for d in nodes.values() if d.get("type") in ["panel", "generic_panel"]])
            inverter_count = len([d for d in nodes.values() if d.get("type") in ["inverter", "generic_inverter"]])
            
            # Placeholder analysis
            placeholder_nodes = {n: d for n, d in nodes.items() if d.get("placeholder", False)}
            real_nodes = {n: d for n, d in nodes.items() if not d.get("placeholder", False)}
            
            has_placeholders = len(placeholder_nodes) > 0
            placeholders_by_type = Counter(d.get("type") for d in placeholder_nodes.values())
            
            placeholder_percentage = 0.0
            if len(nodes) > 0:
                placeholder_percentage = len(placeholder_nodes) / len(nodes) * 100
            
            # Requirements analysis
            requirements = graph.graph.get("requirements", {})
            required_fields = ["target_power", "roof_area", "budget"]
            missing_requirements = [k for k in required_fields if not requirements.get(k)]
            requirements_complete = len(missing_requirements) == 0
            
            # Component availability analysis
            panel_available = await self.component_db_service.exists(category="panel")
            inverter_available = await self.component_db_service.exists(category="inverter")
            components_available = panel_available and inverter_available
            
            # Determine if placeholder design is allowed (when requirements complete but no real components)
            allow_placeholder_design = requirements_complete and not components_available
            
            # Count available replacements for each placeholder type
            available_replacement_count = 0
            if has_placeholders:
                for placeholder_type in placeholders_by_type.keys():
                    if placeholder_type.startswith("generic_"):
                        real_type = placeholder_type.replace("generic_", "")
                        try:
                            replacements = await self.component_db_service.search(category=real_type)
                            available_replacement_count += len(replacements)
                        except Exception:
                            pass
            
            return {
                "has_panels": has_panels,
                "has_inverters": has_inverters,
                "has_mounts": has_mounts,
                "has_wiring": has_wiring,
                "has_batteries": has_batteries,
                "has_monitoring": has_monitoring,
                "panel_count": panel_count,
                "inverter_count": inverter_count,
                "has_preliminary_design": has_panels and has_inverters,
                "has_placeholders": has_placeholders,
                "placeholders_by_type": dict(placeholders_by_type),
                "total_placeholders": len(placeholder_nodes),
                "placeholder_percentage": placeholder_percentage,
                "real_component_count": len(real_nodes),
                "requirements": requirements,
                "missing_requirements": missing_requirements,
                "requirements_complete": requirements_complete,
                "panel_available": panel_available,
                "inverter_available": inverter_available,
                "components_available": components_available,
                "allow_placeholder_design": allow_placeholder_design,
                "available_replacement_count": available_replacement_count,
            }
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error analyzing graph state: {e}", exc_info=True)
            # Return safe defaults
            return {
                "has_panels": False,
                "has_inverters": False,
                "has_mounts": False,
                "has_wiring": False,
                "has_batteries": False,
                "has_monitoring": False,
                "panel_count": 0,
                "inverter_count": 0,
                "has_preliminary_design": False,
                "has_placeholders": False,
                "placeholders_by_type": {},
                "total_placeholders": 0,
                "placeholder_percentage": 0.0,
                "real_component_count": 0,
                "requirements": {},
                "missing_requirements": ["target_power", "roof_area", "budget"],
                "requirements_complete": False,
                "panel_available": False,
                "inverter_available": False,
                "components_available": False,
                "allow_placeholder_design": False,
                "available_replacement_count": 0,
            }

    def _create_placeholder_summary(self, placeholders_by_type: Dict[str, int]) -> str:
        """Create human-readable summary of placeholder components."""
        if not placeholders_by_type:
            return "no placeholders"
        
        parts = []
        for ptype, count in placeholders_by_type.items():
            display_type = ptype.replace("generic_", "").replace("_", " ")
            parts.append(f"{count} {display_type}{'s' if count != 1 else ''}")
        
        return ", ".join(parts)

    def _should_add_battery_design(self, requirements: Dict[str, Any], state: Dict[str, Any]) -> bool:
        """Determine if battery design task should be added."""
        # Add battery design if backup hours specified and no batteries exist
        backup_hours = requirements.get("backup_hours", 0)
        return backup_hours > 0 and not state.get("has_batteries", False)

    def _should_add_monitoring(self, requirements: Dict[str, Any], state: Dict[str, Any]) -> bool:
        """Determine if monitoring system task should be added."""
        # Add monitoring for systems above 1kW and no monitoring exists
        target_power = requirements.get("target_power", 0)
        return target_power > 1000 and not state.get("has_monitoring", False)

    def _estimate_battery_capacity(self, requirements: Dict[str, Any]) -> float:
        """Estimate required battery capacity in kWh."""
        target_power = requirements.get("target_power", 0)
        backup_hours = requirements.get("backup_hours", 8)
        
        if target_power > 0 and backup_hours > 0:
            # Rough estimate: power * hours / 1000 (W to kW)
            return (target_power * backup_hours) / 1000
        
        return 10.0  # Default 10kWh
