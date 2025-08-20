# backend/agents/modern_system_design_agent.py
"""Modern system design agent using the unified enterprise interface."""

from __future__ import annotations

import logging
from typing import Dict, List, Any
from dataclasses import dataclass

from backend.agents.base import (
    UnifiedAgentInterface,
    AgentContext,
    AgentCapabilities,
    AgentResponse
)
from backend.schemas.ai import AiAction, AiActionType
from backend.services.advanced_reasoning_service import (
    get_advanced_reasoning_service,
    ReasoningStrategy,
    ReasoningDepth,
    ReasoningContext as ReasoningContextModel
)


@dataclass
class DesignRequirements:
    """Structured design requirements."""

    target_power: float  # kW
    roof_area: float  # m2
    budget: float  # USD
    location: str = "default"
    efficiency_target: float = 0.8


class ModernSystemDesignAgent(UnifiedAgentInterface):
    """Modern system design agent with advanced reasoning capabilities."""

    name = "modern_system_design_agent"
    description = "Intelligent system design agent using advanced reasoning"
    version = "2.0.0"

    def __init__(self):
        super().__init__()

        # Define capabilities
        self.capabilities = AgentCapabilities(
            can_design=True,
            can_analyze=True,
            can_optimize=True,
            domains=["solar", "hvac", "pumping"],
            risk_level="medium",
            requires_graph_context=False
        )

        # Supported actions
        self.supported_actions = [
            AiActionType.add_component,
            AiActionType.add_link,
            AiActionType.report,
            AiActionType.validation
        ]

        # Initialize services
        self.reasoning_service = get_advanced_reasoning_service()

    async def execute_task(
        self,
        task_id: str,
        context: AgentContext,
        **kwargs: Any
    ) -> AgentResponse:
        """Execute design tasks with advanced reasoning."""

        try:
            # Validate context
            validation_errors = await self.validate_context(context)
            if validation_errors:
                return AgentResponse(
                    success=False,
                    errors=validation_errors
                )

            # Parse command and extract requirements
            command = kwargs.get('command', '')
            requirements = await self._parse_requirements(command, context)

            if not requirements:
                return AgentResponse(
                    success=False,
                    errors=["Could not parse design requirements from command"]
                )

            # Execute reasoning-based design
            reasoning_context = ReasoningContextModel(
                domain="solar",  # Default to solar for now
                task_type="design",
                user_intent=command,
                design_context=context.design_snapshot,
                reasoning_depth=ReasoningDepth.ADVANCED,
                strategy=ReasoningStrategy.CHAIN_OF_THOUGHT
            )

            reasoning_result = await self.reasoning_service.execute_reasoning(
                reasoning_context,
                f"Design a system with: {requirements.target_power}kW, "
                f"{requirements.roof_area}m2 roof, ${requirements.budget} budget"
            )

            # Generate design actions based on reasoning
            actions = await self._generate_design_actions(requirements, reasoning_result)

            return AgentResponse(
                success=True,
                actions=actions,
                confidence_score=reasoning_result.confidence_score,
                explanation=reasoning_result.explanation,
                metadata={
                    "design_requirements": {
                        "target_power": requirements.target_power,
                        "roof_area": requirements.roof_area,
                        "budget": requirements.budget
                    },
                    "reasoning_steps": len(reasoning_result.reasoning_chain.steps)
                }
            )

        except Exception as e:
            self.logger.error(f"Design execution failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                errors=[f"Design failed: {str(e)}"]
            )

    async def _parse_requirements(
        self,
        command: str,
        context: AgentContext
    ) -> DesignRequirements | None:
        """Parse design requirements from command using reasoning."""

        try:
            # Use reasoning to extract structured requirements
            reasoning_context = ReasoningContextModel(
                domain="general",
                task_type="analysis",
                user_intent="Extract design requirements from command",
                reasoning_depth=ReasoningDepth.STANDARD,
                strategy=ReasoningStrategy.BASIC
            )

            prompt = f"""
            Extract design requirements from this command: "{command}"

            Look for:
            - Target power (kW)
            - Roof area (m2)
            - Budget ($)
            - Location
            - Efficiency targets

            Return as structured data.
            """

            result = await self.reasoning_service.execute_reasoning(reasoning_context, prompt)

            # Parse reasoning result into requirements
            # This is a simplified implementation
            target_power = self._extract_value(command, r'(\d+(?:\.\d+)?)\s*(?:kw|kilowatt)', 5.0)
            roof_area = self._extract_value(command, r'(\d+(?:\.\d+)?)\s*(?:m2|sqm|roof)', 100.0)
            budget = self._extract_value(command, r'\$(\d+(?:\.\d+)?)', 50000.0)

            return DesignRequirements(
                target_power=target_power,
                roof_area=roof_area,
                budget=budget
            )

        except Exception as e:
            self.logger.warning(f"Failed to parse requirements: {e}")
            return None

    def _extract_value(self, text: str, pattern: str, default: float) -> float:
        """Extract numeric value from text using regex pattern."""
        import re
        match = re.search(pattern, text, re.IGNORECASE)
        return float(match.group(1)) if match else default

    async def _generate_design_actions(
        self,
        requirements: DesignRequirements,
        reasoning_result: Any
    ) -> List[AiAction]:
        """Generate design actions based on requirements and reasoning."""

        actions = []

        # Calculate component counts
        panel_count = max(1, int((requirements.target_power * 1000) / 400))  # Assume 400W panels
        inverter_count = max(1, int(panel_count / 10))  # 1 inverter per 10 panels

        # Add validation action
        actions.append(AiAction(
            action=AiActionType.validation,
            payload={
                "message": f"Designing {requirements.target_power}kW system for "
                          f"{requirements.roof_area}m² roof within ${requirements.budget} budget"
            },
            version=1
        ))

        # Add panel components
        for i in range(panel_count):
            actions.append(AiAction(
                action=AiActionType.add_component,
                payload={
                    "name": f"Solar Panel {i+1}",
                    "type": "panel",
                    "standard_code": f"PANEL_{i+1}",
                    "x": 100 + (i % 5) * 120,
                    "y": 100 + (i // 5) * 120,
                    "layer": "Single-Line Diagram"
                },
                version=1
            ))

        # Add inverter components
        for i in range(inverter_count):
            actions.append(AiAction(
                action=AiActionType.add_component,
                payload={
                    "name": f"Inverter {i+1}",
                    "type": "inverter",
                    "standard_code": f"INV_{i+1}",
                    "x": 400,
                    "y": 100 + i * 100,
                    "layer": "Single-Line Diagram"
                },
                version=1
            ))

        # Add connections
        panels_per_inverter = panel_count // inverter_count
        for inv_idx in range(inverter_count):
            for panel_idx in range(panels_per_inverter):
                global_panel_idx = inv_idx * panels_per_inverter + panel_idx
                if global_panel_idx < panel_count:
                    actions.append(AiAction(
                        action=AiActionType.add_link,
                        payload={
                            "source_id": f"PANEL_{global_panel_idx}",
                            "target_id": f"INV_{inv_idx}",
                            "connection_type": "electrical"
                        },
                        version=1
                    ))

        # Add design report
        actions.append(AiAction(
            action=AiActionType.report,
            payload={
                "message": f"Generated design: {panel_count} panels, {inverter_count} inverters. "
                          f"Total capacity: {panel_count * 0.4:.1f}kW"
            },
            version=1
        ))

        return actions

    async def explain_action(
        self,
        action: AiAction,
        context: AgentContext
    ) -> str:
        """Provide detailed explanation for design actions."""

        if action.action == AiActionType.add_component:
            component_type = action.payload.get("type", "unknown")
            return f"Adding {component_type} component as part of system design to meet capacity requirements."
        elif action.action == AiActionType.add_link:
            return "Creating electrical connection between components to form a functional system."
        elif action.action == AiActionType.validation:
            return "Validating design parameters against requirements and constraints."
        else:
            return f"Executing {action.action} as part of the system design process."

    async def collaborate_with(
        self,
        other_agents: List[UnifiedAgentInterface],
        task_id: str,
        context: AgentContext
    ) -> AgentResponse:
        """Collaborate with other agents for complex design tasks."""

        if not self.capabilities.supports_collaboration:
            return AgentResponse(
                success=False,
                errors=["This agent does not support collaboration"]
            )

        # For design tasks, collaborate with wiring and structural agents
        collaboration_results = []

        for agent in other_agents:
            if "wiring" in agent.name or "structural" in agent.name:
                result = await agent.execute_task(task_id, context)
                collaboration_results.append(result)

        # Combine results
        combined_actions = []
        for result in collaboration_results:
            if result.success:
                combined_actions.extend(result.actions)

        return AgentResponse(
            success=True,
            actions=combined_actions,
            metadata={"collaboration": True, "agents": len(other_agents)}
        )


# Example of how to register the modern agent
async def register_modern_system_design_agent():
    """Register the modern system design agent."""
    from backend.agents.registry import register, register_spec
    from backend.schemas.ai import AiActionType

    agent = ModernSystemDesignAgent()

    # Register the agent
    register(agent)

    # Register agent specifications
    register_spec(
        name=agent.name,
        domain="design",
        risk_class="medium",
        capabilities=[AiActionType.add_component, AiActionType.add_link, AiActionType.report],
        description=agent.description
    )

    # Initialize the agent
    await agent.initialize()

    return agent
