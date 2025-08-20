# backend/agents/intelligent_router_agent.py
"""Enterprise-grade intelligent router with advanced reasoning capabilities."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from openai import AsyncOpenAI

from backend.agents.base import (
    UnifiedAgentInterface,
    AgentContext,
    AgentCapabilities,
    AgentResponse
)
from backend.agents.registry import get_agent, get_agent_names
from backend.services.ai_clients import get_openai_client
from backend.services.advanced_reasoning_service import (
    get_advanced_reasoning_service,
    ReasoningStrategy,
    ReasoningDepth,
    ReasoningContext as ReasoningContextModel
)
from backend.utils.logging import get_logger


logger = get_logger(__name__)


@dataclass
class RoutingDecision:
    """Intelligent routing decision with reasoning."""

    primary_agent: str
    supporting_agents: List[str] = field(default_factory=list)
    reasoning_strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT
    reasoning_depth: ReasoningDepth = ReasoningDepth.STANDARD
    confidence: float = 0.0
    reasoning_explanation: str = ""
    parallel_execution: bool = False


@dataclass
class RoutingContext:
    """Enhanced context for intelligent routing."""

    user_query: str
    domain: str
    complexity: str  # simple, moderate, complex
    urgency: str  # low, medium, high
    required_capabilities: Set[str] = field(default_factory=set)


class IntelligentRouterAgent(UnifiedAgentInterface):
    """Enterprise-grade intelligent router with advanced reasoning capabilities."""

    name = "intelligent_router_agent"
    description = "Advanced AI router that intelligently orchestrates agent execution with reasoning and optimization."
    version = "2.0.0"

    def __init__(self, client: AsyncOpenAI | None = None):
        super().__init__()
        self.capabilities = AgentCapabilities(
            can_design=True,
            can_analyze=True,
            can_validate=True,
            can_optimize=True,
            domains=["routing", "orchestration", "coordination"],
            risk_level="low",
            supports_streaming=True,
            supports_collaboration=True,
            supports_explanation=True
        )
        self.supported_actions = []  # Router doesn't perform actions directly

        self._client = client or get_openai_client()
        self.reasoning_service = get_advanced_reasoning_service()

        # Enhanced routing knowledge base
        self._routing_patterns = self._initialize_routing_patterns()

    def _initialize_routing_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize intelligent routing patterns with domain knowledge."""

        return {
            # Design patterns
            "design": {
                "keywords": ["design", "create", "build", "develop", "generate"],
                "primary_agents": ["system_design_agent", "pv_design_agent"],
                "supporting_agents": ["wiring_agent", "structural_agent", "monitoring_agent"],
                "reasoning_strategy": ReasoningStrategy.CHAIN_OF_THOUGHT,
                "reasoning_depth": ReasoningDepth.ADVANCED
            },

            # Component management patterns
            "component": {
                "keywords": ["add", "remove", "delete", "component", "panel", "inverter", "battery"],
                "primary_agents": ["component_agent"],
                "supporting_agents": ["inventory_agent"],
                "reasoning_strategy": ReasoningStrategy.REACTIVE,
                "reasoning_depth": ReasoningDepth.STANDARD
            },

            # Analysis patterns
            "analysis": {
                "keywords": ["analyze", "validate", "check", "verify", "performance", "efficiency"],
                "primary_agents": ["performance_agent", "cross_layer_validation_agent"],
                "supporting_agents": ["learning_agent"],
                "reasoning_strategy": ReasoningStrategy.MULTI_PERSPECTIVE,
                "reasoning_depth": ReasoningDepth.ADVANCED
            },

            # Documentation patterns
            "documentation": {
                "keywords": ["bom", "bill", "materials", "report", "document"],
                "primary_agents": ["bom_agent"],
                "reasoning_strategy": ReasoningStrategy.BASIC,
                "reasoning_depth": ReasoningDepth.STANDARD
            }
        }

    async def execute_task(
        self,
        task_id: str,
        context: AgentContext,
        **kwargs: Any
    ) -> AgentResponse:
        """Execute intelligent routing with advanced reasoning."""

        try:
            # Analyze the user query and context
            routing_context = await self._analyze_routing_context(
                kwargs.get('command', ''),
                context
            )

            # Make intelligent routing decision
            routing_decision = await self._make_routing_decision(routing_context)

            # Execute routing with reasoning
            result = await self._execute_routing_with_reasoning(
                routing_decision,
                context,
                kwargs
            )

            return result

        except Exception as e:
            logger.error(f"Intelligent routing failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                errors=[f"Routing failed: {str(e)}"],
                explanation=f"Unable to route request: {str(e)}"
            )

    async def _analyze_routing_context(
        self,
        command: str,
        context: AgentContext
    ) -> RoutingContext:
        """Analyze the routing context with intelligent pattern matching."""

        # Determine domain from command
        domain = await self._classify_domain(command)

        # Assess complexity
        complexity = self._assess_complexity(command)

        # Determine urgency
        urgency = self._assess_urgency(command)

        # Extract required capabilities
        required_capabilities = await self._extract_required_capabilities(command, domain)

        return RoutingContext(
            user_query=command,
            domain=domain,
            complexity=complexity,
            urgency=urgency,
            required_capabilities=required_capabilities
        )

    async def _classify_domain(self, command: str) -> str:
        """Classify the domain using intelligent pattern matching."""

        command_lower = command.lower()

        # Domain classification with intelligent matching
        domain_patterns = {
            "solar": ["solar", "pv", "photovoltaic", "panel", "inverter"],
            "hvac": ["hvac", "air conditioning", "heating", "cooling", "compressor"],
            "pumping": ["pump", "water", "pumping", "well", "irrigation"],
            "structural": ["mount", "structure", "roof", "ground", "rack"],
            "electrical": ["wire", "cable", "electrical", "connection", "fuse"],
            "monitoring": ["monitor", "sensor", "telemetry", "data", "logging"],
            "battery": ["battery", "storage", "energy", "backup", "power"],
            "network": ["network", "communication", "connectivity", "protocol"],
            "financial": ["cost", "price", "budget", "finance", "money"],
            "documentation": ["bom", "bill", "materials", "report", "document"]
        }

        domain_scores = {}
        for domain, keywords in domain_patterns.items():
            score = sum(1 for keyword in command_lower if keyword in command_lower)
            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            return max(domain_scores.keys(), key=lambda x: domain_scores[x])

        return "general"

    def _assess_complexity(self, command: str) -> str:
        """Assess the complexity of the command."""

        # Simple indicators
        simple_indicators = ["add", "remove", "show", "list", "get", "find"]
        complex_indicators = ["design", "optimize", "analyze", "create", "develop", "system"]

        command_lower = command.lower()
        word_count = len(command.split())

        # Check for complexity indicators
        has_complex_keywords = any(indicator in command_lower for indicator in complex_indicators)
        has_simple_keywords = any(indicator in command_lower for indicator in simple_indicators)

        if word_count > 20 or has_complex_keywords:
            return "complex"
        elif word_count > 10 or (has_simple_keywords and word_count > 5):
            return "moderate"
        else:
            return "simple"

    def _assess_urgency(self, command: str) -> str:
        """Assess the urgency level of the command."""

        urgency_indicators = {
            "high": ["urgent", "asap", "immediately", "critical", "emergency"],
            "medium": ["soon", "quick", "fast", "important"],
            "low": ["when possible", "eventually", "later", "whenever"]
        }

        command_lower = command.lower()

        for level, indicators in urgency_indicators.items():
            if any(indicator in command_lower for indicator in indicators):
                return level

        return "medium"  # Default urgency

    async def _extract_required_capabilities(self, command: str, domain: str) -> Set[str]:
        """Extract required agent capabilities from the command."""

        required_capabilities = set()
        command_lower = command.lower()

        # Map command patterns to required capabilities
        capability_patterns = {
            "can_design": ["design", "create", "build", "generate", "develop"],
            "can_analyze": ["analyze", "validate", "check", "verify", "assess"],
            "can_optimize": ["optimize", "improve", "cost", "efficiency", "performance"],
            "requires_graph_context": ["design", "system", "layout", "structure"],
            "supports_collaboration": ["complex", "system", "integrated", "comprehensive"]
        }

        for capability, patterns in capability_patterns.items():
            if any(pattern in command_lower for pattern in patterns):
                required_capabilities.add(capability)

        return required_capabilities

    async def _make_routing_decision(self, routing_context: RoutingContext) -> RoutingDecision:
        """Make intelligent routing decision based on context analysis."""

        # Match against routing patterns
        best_pattern = None
        best_score = 0

        for pattern_name, pattern_config in self._routing_patterns.items():
            score = self._calculate_pattern_match_score(routing_context, pattern_config)
            if score > best_score:
                best_score = score
                best_pattern = pattern_name

        if best_pattern:
            pattern_config = self._routing_patterns[best_pattern]

            # Use advanced reasoning to refine the decision
            reasoning_context = ReasoningContextModel(
                domain=routing_context.domain,
                task_type="routing",
                user_intent=routing_context.user_query,
                reasoning_depth=pattern_config["reasoning_depth"],
                strategy=pattern_config["reasoning_strategy"]
            )

            reasoning_result = await self.reasoning_service.execute_reasoning(
                reasoning_context,
                f"Route this request: {routing_context.user_query}"
            )

            return RoutingDecision(
                primary_agent=pattern_config["primary_agents"][0],
                supporting_agents=pattern_config["supporting_agents"],
                reasoning_strategy=pattern_config["reasoning_strategy"],
                reasoning_depth=pattern_config["reasoning_depth"],
                confidence=reasoning_result.confidence_score,
                reasoning_explanation=reasoning_result.explanation,
                parallel_execution=routing_context.complexity == "complex"
            )

        # Fallback to basic routing
        return await self._fallback_routing(routing_context)

    def _calculate_pattern_match_score(self, context: RoutingContext, pattern: Dict[str, Any]) -> float:
        """Calculate how well a routing pattern matches the context."""

        score = 0.0

        # Keyword matching
        command_lower = context.user_query.lower()
        for keyword in pattern["keywords"]:
            if keyword in command_lower:
                score += 1.0

        # Domain matching
        if context.domain in pattern.get("domain_match", []):
            score += 2.0

        # Complexity matching
        if context.complexity == pattern.get("complexity_preference", context.complexity):
            score += 0.5

        # Capability matching
        pattern_capabilities = pattern.get("required_capabilities", set())
        if pattern_capabilities.issubset(context.required_capabilities):
            score += 1.0

        return score

    async def _fallback_routing(self, context: RoutingContext) -> RoutingDecision:
        """Fallback routing when pattern matching fails."""

        # Use LLM for intelligent fallback routing
        fallback_prompt = f"""
        Analyze this user request and determine the most appropriate agent to handle it:

        Request: {context.user_query}
        Domain: {context.domain}
        Complexity: {context.complexity}

        Available agents: {', '.join(get_agent_names())}

        Return a JSON object with:
        - primary_agent: the main agent to handle this
        - supporting_agents: list of additional agents if needed
        - confidence: confidence score (0.0-1.0)
        - reasoning: brief explanation
        """

        try:
            response = await self._client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at routing engineering design requests to appropriate AI agents."},
                    {"role": "user", "content": fallback_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            result = json.loads(response.choices[0].message.content)

            return RoutingDecision(
                primary_agent=result.get("primary_agent", "system_design_agent"),
                supporting_agents=result.get("supporting_agents", []),
                confidence=result.get("confidence", 0.5),
                reasoning_explanation=result.get("reasoning", "LLM-based routing")
            )

        except Exception as e:
            logger.error(f"Fallback routing failed: {e}")
            return RoutingDecision(
                primary_agent="system_design_agent",
                confidence=0.3,
                reasoning_explanation="Fallback to default agent due to routing error"
            )

    async def _execute_routing_with_reasoning(
        self,
        decision: RoutingDecision,
        context: AgentContext,
        kwargs: Dict[str, Any]
    ) -> AgentResponse:
        """Execute the routing decision with intelligent orchestration."""

        actions = []
        errors = []
        explanations = []

        try:
            # Get primary agent
            primary_agent = self._get_agent(decision.primary_agent)

            if primary_agent:
                # Execute primary agent with reasoning context
                primary_context = AgentContext(
                    session_id=context.session_id,
                    tenant_id=context.tenant_id,
                    user_id=context.user_id,
                    trace_id=context.trace_id,
                    design_snapshot=context.design_snapshot,
                    recent_actions=context.recent_actions,
                    reasoning_depth=decision.reasoning_depth,
                    collaboration_mode=len(decision.supporting_agents) > 0
                )

                primary_result = await primary_agent.execute_task(
                    task_id="routed_request",
                    context=primary_context,
                    command=kwargs.get('command', ''),
                    reasoning_context=decision.reasoning_explanation
                )

                if primary_result.success:
                    actions.extend(primary_result.actions)
                    explanations.append(f"Primary agent ({decision.primary_agent}): {primary_result.explanation}")
                else:
                    errors.extend(primary_result.errors)

            # Execute supporting agents if needed
            if decision.supporting_agents:
                supporting_results = await self._execute_supporting_agents_sequential(
                    decision.supporting_agents,
                    context,
                    kwargs
                )
                for agent_name, result in supporting_results.items():
                    if result.success:
                        actions.extend(result.actions)
                        explanations.append(f"Supporting agent ({agent_name}): {result.explanation}")
                    else:
                        errors.extend(result.errors)

            return AgentResponse(
                success=len(errors) == 0,
                actions=actions,
                confidence_score=decision.confidence,
                explanation="\n".join(explanations),
                errors=errors,
                metadata={
                    "routing_decision": {
                        "primary_agent": decision.primary_agent,
                        "supporting_agents": decision.supporting_agents,
                        "reasoning_strategy": decision.reasoning_strategy.value,
                        "confidence": decision.confidence,
                        "parallel_execution": decision.parallel_execution
                    }
                }
            )

        except Exception as e:
            logger.error(f"Routing execution failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                errors=[f"Routing execution failed: {str(e)}"],
                explanation=f"Failed to execute routing decision: {str(e)}"
            )

    def _get_agent(self, agent_name: str) -> Optional[UnifiedAgentInterface]:
        """Get an agent by name."""

        try:
            agent = get_agent(agent_name)
            if isinstance(agent, UnifiedAgentInterface):
                return agent
            else:
                logger.warning(f"Agent {agent_name} is not a UnifiedAgentInterface")
                return None
        except Exception as e:
            logger.warning(f"Failed to get agent {agent_name}: {e}")
            return None

    async def _execute_supporting_agents_sequential(
        self,
        agent_names: List[str],
        context: AgentContext,
        kwargs: Dict[str, Any]
    ) -> Dict[str, AgentResponse]:
        """Execute supporting agents sequentially."""

        results = {}
        for agent_name in agent_names:
            agent = self._get_agent(agent_name)
            if agent:
                try:
                    results[agent_name] = await agent.execute_task(
                        task_id="supporting_request",
                        context=context,
                        **kwargs
                    )
                except Exception as e:
                    logger.error(f"Supporting agent {agent_name} failed: {e}")
                    results[agent_name] = AgentResponse(
                        success=False,
                        errors=[str(e)]
                    )

        return results
