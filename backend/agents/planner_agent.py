"""Task planner that inspects session state and requirements."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from backend.services import odl_graph_service
from backend.services.component_db_service import ComponentDBService
from backend.services.ai_clients import get_openai_client

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
        self.openai_client = get_openai_client()

    async def plan(
        self, session_id: str, command: str, *, requirements: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Dynamically produce a list of tasks based on the current session state
        and user intent. This enhanced version performs deeper analysis of the
        graph state and requirements to emit contextually appropriate tasks.

        Task Decision Logic:
        - gather_requirements: emitted if any required user input or component
          datasheets are missing.
        - generate_design: emitted only if no panel/inverter combination exists
          AND requirements are complete.
        - generate_structural: emitted after panels exist but mounts are missing.
        - generate_wiring: emitted after design exists but wiring is missing.
        - refine_validate: always emitted as final step when design exists.

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
        if not cmd.startswith("design"):
            return []

        # Get current graph and analyze its state
        graph = await self.odl_graph_service.get_graph(session_id)
        if not graph:
            # If no graph exists, create one
            graph = await self.odl_graph_service.create_graph(session_id)

        # Enhanced graph state analysis
        has_panels = any(d.get("type") == "panel" for _, d in graph.nodes(data=True))
        has_inverters = any(d.get("type") == "inverter" for _, d in graph.nodes(data=True))
        has_mounts = any(d.get("type") == "mount" for _, d in graph.nodes(data=True))
        has_wiring = any(d.get("type") in {"cable", "fuse"} for _, d in graph.nodes(data=True))
        
        # Count existing components for better decision making
        panel_count = len([d for _, d in graph.nodes(data=True) if d.get("type") == "panel"])
        inverter_count = len([d for _, d in graph.nodes(data=True) if d.get("type") == "inverter"])
        
        # Check requirements completeness
        reqs = graph.graph.get("requirements", {})
        required_fields = ["target_power", "roof_area", "budget"]
        missing_requirements = [k for k in required_fields if not reqs.get(k)]
        requirements_complete = len(missing_requirements) == 0
        
        # Enhanced component availability checking
        panel_available = await self.component_db_service.exists(category="panel")
        inverter_available = await self.component_db_service.exists(category="inverter")
        components_available = panel_available and inverter_available
        
        # Check if we have a complete preliminary design
        has_preliminary_design = has_panels and has_inverters

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

        # Phase 1: Gather Requirements (always first if incomplete)
        if not requirements_complete or not components_available:
            gather_status = "pending"  # This is always actionable by user
            missing_items = []
            if missing_requirements:
                missing_items.extend(missing_requirements)
            if not components_available:
                if not panel_available:
                    missing_items.append("panel datasheet")
                if not inverter_available:
                    missing_items.append("inverter datasheet")
            
            tasks.append({
                "id": "gather_requirements",
                "status": gather_status,
                "reason": f"Missing: {', '.join(missing_items)}",
                "missing_requirements": missing_requirements,
                "missing_components": [] if components_available else ["panel", "inverter"]
            })

        # Phase 2: Generate Design (only if no preliminary design exists)
        if not has_preliminary_design:
            if requirements_complete and components_available:
                design_status = "pending"
                design_reason = "Ready to generate preliminary design"
            else:
                design_status = "blocked"
                blockers = []
                if not requirements_complete:
                    blockers.append("requirements incomplete")
                if not components_available:
                    blockers.append("components unavailable")
                design_reason = f"Blocked by: {', '.join(blockers)}"
            
            tasks.append({
                "id": "generate_design",
                "status": design_status,
                "reason": design_reason,
                "estimated_panels": panel_count if panel_count > 0 else reqs.get("panel_count_estimate", 1),
                "estimated_inverters": inverter_count if inverter_count > 0 else reqs.get("inverter_count_estimate", 1)
            })

        # Phase 3: Structural Design (only after preliminary design exists)
        if has_preliminary_design and not has_mounts:
            tasks.append({
                "id": "generate_structural",
                "status": "pending",
                "reason": f"Generate mounting for {panel_count} panel{'s' if panel_count != 1 else ''}"
            })

        # Phase 4: Wiring Design (only after preliminary design exists)
        if has_preliminary_design and not has_wiring:
            tasks.append({
                "id": "generate_wiring",
                "status": "pending",
                "reason": f"Generate wiring between {panel_count} panel{'s' if panel_count != 1 else ''} and {inverter_count} inverter{'s' if inverter_count != 1 else ''}"
            })

        # Phase 5: Refine and Validate (always last when design exists)
        if has_preliminary_design:
            validation_status = "pending"
            completion_items = []
            if has_mounts:
                completion_items.append("structural")
            if has_wiring:
                completion_items.append("wiring")
            
            if completion_items:
                validation_reason = f"Validate design with {', '.join(completion_items)}"
            else:
                validation_reason = "Validate preliminary design"
            
            tasks.append({
                "id": "refine_validate",
                "status": validation_status,
                "reason": validation_reason,
                "design_completeness": len(completion_items) / 2.0  # structural + wiring
            })

        # Enhance all tasks with titles and context
        for task in tasks:
            tid = task["id"]
            task["title"] = TASK_TITLES.get(tid, tid.replace("_", " ").title())
            
            # Add graph summary for context
            if "graph_summary" not in task:
                task["graph_summary"] = odl_graph_service.describe_graph(graph)

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
- generate_structural: Use after panels placed but missing mounting
- generate_wiring: Use after design exists but missing electrical connections
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
                "generate_wiring", "refine_validate"
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
            print(f"LLM-enhanced planning failed: {e}")
            return None
        
        return None
