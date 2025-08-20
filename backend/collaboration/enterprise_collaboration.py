# backend/collaboration/enterprise_collaboration.py
"""Enterprise-grade multi-agent collaboration framework for OriginFlow AI platform."""

from __future__ import annotations

import asyncio
import logging
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid

from backend.agents.base import (
    UnifiedAgentInterface,
    AgentContext,
    AgentResponse,
    AgentCapabilities
)
from backend.services.advanced_reasoning_service import (
    get_advanced_reasoning_service,
    ReasoningStrategy,
    ReasoningDepth,
    ReasoningContext as ReasoningContextModel
)
from backend.utils.logging import get_logger
from backend.utils.observability import trace_span, record_metric


logger = get_logger(__name__)


class CollaborationMode(Enum):
    """Different collaboration modes available."""

    SEQUENTIAL = "sequential"  # Agents work one after another
    PARALLEL = "parallel"      # Agents work simultaneously
    HIERARCHICAL = "hierarchical"  # Master-slave relationship
    MARKETPLACE = "marketplace"    # Bidding-based collaboration
    CONSENSUS = "consensus"        # Democratic decision making


class CollaborationStrategy(Enum):
    """Strategies for agent collaboration."""

    SPECIALIZATION = "specialization"  # Each agent handles specific domain
    ROUND_ROBIN = "round_robin"       # Rotate through agents
    EXPERTISE_BASED = "expertise"     # Route to most qualified agent
    COLLABORATIVE = "collaborative"   # All agents contribute equally
    COMPETITIVE = "competitive"       # Best solution wins


@dataclass
class CollaborationContext:
    """Context for multi-agent collaboration."""

    collaboration_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mode: CollaborationMode = CollaborationMode.SEQUENTIAL
    strategy: CollaborationStrategy = CollaborationStrategy.SPECIALIZATION
    max_participants: int = 10
    timeout_seconds: float = 300.0
    consensus_threshold: float = 0.7
    allow_conflicts: bool = True
    require_explanation: bool = True

    # Enterprise features
    tenant_id: str = "default"
    security_context: Optional[Dict[str, Any]] = None
    compliance_requirements: Set[str] = field(default_factory=set)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CollaborationTask:
    """Task definition for collaboration."""

    task_id: str
    description: str
    domain: str
    complexity: str = "medium"
    priority: str = "normal"
    required_capabilities: Set[str] = field(default_factory=set)
    constraints: Dict[str, Any] = field(default_factory=dict)
    deadline: Optional[datetime] = None

    # Collaboration-specific
    collaboration_context: Optional[CollaborationContext] = None
    subtasks: List['CollaborationTask'] = field(default_factory=list)


@dataclass
class CollaborationResult:
    """Result of a collaboration session."""

    success: bool
    final_result: AgentResponse
    participants: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    confidence_score: float = 0.0
    conflicts_resolved: int = 0
    consensus_reached: bool = True
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnterpriseCollaborationManager:
    """Enterprise-grade collaboration manager for multi-agent systems."""

    def __init__(self):
        self.reasoning_service = get_advanced_reasoning_service()
        self.logger = logging.getLogger(f"{__name__}.EnterpriseCollaborationManager")

        # Collaboration patterns and templates
        self._collaboration_patterns = self._initialize_patterns()
        self._active_collaborations: Dict[str, CollaborationContext] = {}

    def _initialize_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize collaboration patterns for different scenarios."""

        return {
            "design_review": {
                "mode": CollaborationMode.SEQUENTIAL,
                "strategy": CollaborationStrategy.SPECIALIZATION,
                "required_agents": ["system_design_agent", "wiring_agent", "structural_agent"],
                "max_participants": 5,
                "consensus_threshold": 0.8
            },
            "optimization_task": {
                "mode": CollaborationMode.PARALLEL,
                "strategy": CollaborationStrategy.COMPETITIVE,
                "required_agents": ["performance_agent", "financial_agent", "learning_agent"],
                "max_participants": 3,
                "consensus_threshold": 0.6
            },
            "complex_analysis": {
                "mode": CollaborationMode.HIERARCHICAL,
                "strategy": CollaborationStrategy.EXPERTISE_BASED,
                "required_agents": ["cross_layer_validation_agent", "auditor_agent"],
                "max_participants": 4,
                "consensus_threshold": 0.9
            },
            "emergency_response": {
                "mode": CollaborationMode.PARALLEL,
                "strategy": CollaborationStrategy.SPECIALIZATION,
                "required_agents": ["monitoring_agent", "learning_agent", "system_design_agent"],
                "max_participants": 6,
                "consensus_threshold": 0.7,
                "timeout_seconds": 60.0
            }
        }

    @asynccontextmanager
    async def collaboration_session(
        self,
        task: CollaborationTask,
        available_agents: List[UnifiedAgentInterface]
    ):
        """Execute a collaboration session with enterprise features."""

        # Initialize collaboration context
        context = task.collaboration_context or CollaborationContext()
        context.tenant_id = getattr(task, 'tenant_id', 'default')

        self._active_collaborations[context.collaboration_id] = context

        start_time = asyncio.get_event_loop().time()

        try:
            # Select appropriate collaboration pattern
            pattern = self._select_collaboration_pattern(task)
            context.mode = pattern["mode"]
            context.strategy = pattern["strategy"]

            # Select participating agents
            participants = await self._select_participants(
                task, available_agents, pattern
            )

            if not participants:
                raise Exception("No suitable agents found for collaboration")

            # Execute collaboration
            result = await self._execute_collaboration(
                task, participants, context
            )

            # Calculate execution metrics
            execution_time = asyncio.get_event_loop().time() - start_time
            result.execution_time = execution_time
            result.participants = [agent.name for agent in participants]

            yield result

        finally:
            # Cleanup
            if context.collaboration_id in self._active_collaborations:
                del self._active_collaborations[context.collaboration_id]

    async def _select_collaboration_pattern(self, task: CollaborationTask) -> Dict[str, Any]:
        """Select the most appropriate collaboration pattern for the task."""

        # Use reasoning to determine optimal pattern
        reasoning_context = ReasoningContextModel(
            domain="collaboration",
            task_type="pattern_selection",
            user_intent=f"Select collaboration pattern for: {task.description}",
            reasoning_depth=ReasoningDepth.STANDARD,
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT
        )

        prompt = f"""
        Analyze this task and select the optimal collaboration pattern:

        Task: {task.description}
        Domain: {task.domain}
        Complexity: {task.complexity}
        Priority: {task.priority}

        Available patterns:
        - design_review: Sequential specialization for design tasks
        - optimization_task: Parallel competition for optimization
        - complex_analysis: Hierarchical expertise for analysis
        - emergency_response: Parallel specialization for urgent tasks

        Consider:
        - Task requirements and constraints
        - Required agent capabilities
        - Time sensitivity and deadlines
        - Collaboration complexity needed

        Return the most appropriate pattern name.
        """

        reasoning_result = await self.reasoning_service.execute_reasoning(
            reasoning_context, prompt
        )

        # Extract pattern from reasoning result
        pattern_name = self._extract_pattern_from_reasoning(reasoning_result)
        return self._collaboration_patterns.get(pattern_name, self._collaboration_patterns["design_review"])

    def _extract_pattern_from_reasoning(self, reasoning_result: Any) -> str:
        """Extract collaboration pattern from reasoning result."""

        result_text = reasoning_result.reasoning_chain.steps[-1].thought.lower() if reasoning_result.reasoning_chain.steps else ""

        for pattern_name in self._collaboration_patterns.keys():
            if pattern_name in result_text:
                return pattern_name

        return "design_review"  # Default fallback

    async def _select_participants(
        self,
        task: CollaborationTask,
        available_agents: List[UnifiedAgentInterface],
        pattern: Dict[str, Any]
    ) -> List[UnifiedAgentInterface]:
        """Select the most appropriate agents for the collaboration."""

        required_agent_names = pattern.get("required_agents", [])
        max_participants = pattern.get("max_participants", 10)

        selected_agents = []

        # First, include required agents if available
        for agent_name in required_agent_names:
            for agent in available_agents:
                if agent.name == agent_name and agent.capabilities.supports_collaboration:
                    selected_agents.append(agent)
                    break

        # Fill remaining slots with suitable agents
        remaining_slots = max_participants - len(selected_agents)

        if remaining_slots > 0:
            suitable_agents = [
                agent for agent in available_agents
                if agent not in selected_agents
                and agent.capabilities.supports_collaboration
                and self._agent_matches_task(agent, task)
            ]

            # Sort by expertise match
            suitable_agents.sort(
                key=lambda a: self._calculate_expertise_match(a, task),
                reverse=True
            )

            selected_agents.extend(suitable_agents[:remaining_slots])

        return selected_agents

    def _agent_matches_task(self, agent: UnifiedAgentInterface, task: CollaborationTask) -> bool:
        """Check if agent is suitable for the task."""

        # Check domain match
        if task.domain not in agent.capabilities.domains:
            return False

        # Check required capabilities
        agent_capabilities = {
            "can_design", "can_analyze", "can_validate", "can_optimize"
        }
        agent_cap_set = {
            attr for attr in agent_capabilities
            if getattr(agent.capabilities, attr, False)
        }

        if not task.required_capabilities.issubset(agent_cap_set):
            return False

        # Check risk compatibility
        if task.complexity == "high" and agent.capabilities.risk_level == "low":
            return False

        return True

    def _calculate_expertise_match(self, agent: UnifiedAgentInterface, task: CollaborationTask) -> float:
        """Calculate how well agent's expertise matches the task."""

        match_score = 0.0

        # Domain match (40% weight)
        if task.domain in agent.capabilities.domains:
            match_score += 0.4

        # Capability match (30% weight)
        matching_capabilities = task.required_capabilities.intersection({
            attr for attr in ["can_design", "can_analyze", "can_validate", "can_optimize"]
            if getattr(agent.capabilities, attr, False)
        })
        capability_score = len(matching_capabilities) / max(len(task.required_capabilities), 1)
        match_score += capability_score * 0.3

        # Risk compatibility (20% weight)
        risk_scores = {"low": 0.3, "medium": 0.7, "high": 1.0, "critical": 0.8}
        risk_compatibility = risk_scores.get(agent.capabilities.risk_level, 0.5)
        if task.complexity == "high":
            risk_compatibility *= 1.2  # Boost high-risk agents for complex tasks
        match_score += risk_compatibility * 0.2

        # Collaboration capability (10% weight)
        if agent.capabilities.supports_collaboration:
            match_score += 0.1

        return min(match_score, 1.0)

    async def _execute_collaboration(
        self,
        task: CollaborationTask,
        participants: List[UnifiedAgentInterface],
        context: CollaborationContext
    ) -> CollaborationResult:
        """Execute the collaboration based on the selected mode and strategy."""

        # Create agent execution context
        agent_context = AgentContext(
            session_id=f"collab_{context.collaboration_id}",
            tenant_id=context.tenant_id,
            collaboration_mode=True
        )

        if context.mode == CollaborationMode.SEQUENTIAL:
            result = await self._execute_sequential_collaboration(
                task, participants, agent_context, context
            )
        elif context.mode == CollaborationMode.PARALLEL:
            result = await self._execute_parallel_collaboration(
                task, participants, agent_context, context
            )
        elif context.mode == CollaborationMode.HIERARCHICAL:
            result = await self._execute_hierarchical_collaboration(
                task, participants, agent_context, context
            )
        else:
            result = await self._execute_sequential_collaboration(
                task, participants, agent_context, context
            )

        return result

    async def _execute_sequential_collaboration(
        self,
        task: CollaborationTask,
        participants: List[UnifiedAgentInterface],
        agent_context: AgentContext,
        collab_context: CollaborationContext
    ) -> CollaborationResult:
        """Execute collaboration where agents work sequentially."""

        all_actions = []
        all_confidences = []
        audit_trail = []

        for i, agent in enumerate(participants):
            try:
                # Add previous results to context for next agent
                if i > 0:
                    agent_context.recent_actions = [
                        {"agent": participants[j].name, "actions": all_actions[j]}
                        for j in range(i)
                    ]

                result = await agent.execute_task(
                    task_id=task.task_id,
                    context=agent_context,
                    command=task.description
                )

                all_actions.append(result.actions)
                all_confidences.append(result.confidence_score)

                audit_trail.append({
                    "agent": agent.name,
                    "step": i + 1,
                    "success": result.success,
                    "actions_count": len(result.actions),
                    "confidence": result.confidence_score,
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                audit_trail.append({
                    "agent": agent.name,
                    "step": i + 1,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })

        # Combine results
        combined_actions = []
        for action_list in all_actions:
            combined_actions.extend(action_list)

        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.5

        # Create final response
        final_response = AgentResponse(
            success=len(all_confidences) > 0,
            actions=combined_actions,
            confidence_score=avg_confidence,
            explanation=f"Sequential collaboration completed with {len(participants)} agents",
            metadata={
                "collaboration_mode": "sequential",
                "participants_count": len(participants)
            }
        )

        return CollaborationResult(
            success=final_response.success,
            final_result=final_response,
            participants=[agent.name for agent in participants],
            confidence_score=avg_confidence,
            audit_trail=audit_trail,
            metadata={"collaboration_strategy": "sequential"}
        )

    async def _execute_parallel_collaboration(
        self,
        task: CollaborationTask,
        participants: List[UnifiedAgentInterface],
        agent_context: AgentContext,
        collab_context: CollaborationContext
    ) -> CollaborationResult:
        """Execute collaboration where agents work in parallel."""

        # Execute all agents simultaneously
        tasks = []
        for agent in participants:
            task_coro = agent.execute_task(
                task_id=task.task_id,
                context=agent_context,
                command=task.description
            )
            tasks.append(task_coro)

        # Wait for all to complete (with timeout)
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=collab_context.timeout_seconds
            )
        except asyncio.TimeoutError:
            # Handle timeout - some agents may still be running
            results = ["timeout"] * len(participants)

        # Process results
        all_actions = []
        all_confidences = []
        audit_trail = []

        for i, (agent, result) in enumerate(zip(participants, results)):
            if isinstance(result, Exception):
                audit_trail.append({
                    "agent": agent.name,
                    "success": False,
                    "error": str(result),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                all_actions.append(result.actions)
                all_confidences.append(result.confidence_score)
                audit_trail.append({
                    "agent": agent.name,
                    "success": result.success,
                    "actions_count": len(result.actions),
                    "confidence": result.confidence_score,
                    "timestamp": datetime.now().isoformat()
                })

        # Combine results using consensus mechanism
        combined_actions = await self._consensus_mechanism(
            all_actions, collab_context.consensus_threshold
        )

        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.5

        final_response = AgentResponse(
            success=len(all_confidences) > 0,
            actions=combined_actions,
            confidence_score=avg_confidence,
            explanation=f"Parallel collaboration completed with {len(participants)} agents",
            metadata={
                "collaboration_mode": "parallel",
                "participants_count": len(participants)
            }
        )

        return CollaborationResult(
            success=final_response.success,
            final_result=final_response,
            participants=[agent.name for agent in participants],
            confidence_score=avg_confidence,
            audit_trail=audit_trail,
            metadata={"collaboration_strategy": "parallel"}
        )

    async def _execute_hierarchical_collaboration(
        self,
        task: CollaborationTask,
        participants: List[UnifiedAgentInterface],
        agent_context: AgentContext,
        collab_context: CollaborationContext
    ) -> CollaborationResult:
        """Execute hierarchical collaboration with master-slave relationships."""

        if not participants:
            return CollaborationResult(success=False, final_result=AgentResponse(success=False))

        # First agent is the master
        master_agent = participants[0]
        slave_agents = participants[1:]

        # Master agent coordinates the work
        master_context = AgentContext(
            session_id=agent_context.session_id,
            tenant_id=agent_context.tenant_id,
            collaboration_mode=True,
            design_snapshot=agent_context.design_snapshot
        )

        master_result = await master_agent.execute_task(
            task_id=f"{task.task_id}_master",
            context=master_context,
            command=f"Coordinate task execution: {task.description}"
        )

        if not master_result.success:
            return CollaborationResult(
                success=False,
                final_result=master_result,
                participants=[agent.name for agent in participants]
            )

        # Execute slave tasks based on master coordination
        slave_tasks = []
        for slave_agent in slave_agents:
            slave_task = slave_agent.execute_task(
                task_id=f"{task.task_id}_slave",
                context=agent_context,
                command=f"Execute subtask based on master coordination: {task.description}"
            )
            slave_tasks.append(slave_task)

        slave_results = await asyncio.gather(*slave_tasks, return_exceptions=True)

        # Combine master and slave results
        all_actions = [master_result.actions]
        all_confidences = [master_result.confidence_score]
        audit_trail = [{
            "agent": master_agent.name,
            "role": "master",
            "success": master_result.success,
            "actions_count": len(master_result.actions),
            "confidence": master_result.confidence_score,
            "timestamp": datetime.now().isoformat()
        }]

        for agent, result in zip(slave_agents, slave_results):
            if isinstance(result, Exception):
                audit_trail.append({
                    "agent": agent.name,
                    "role": "slave",
                    "success": False,
                    "error": str(result),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                all_actions.append(result.actions)
                all_confidences.append(result.confidence_score)
                audit_trail.append({
                    "agent": agent.name,
                    "role": "slave",
                    "success": result.success,
                    "actions_count": len(result.actions),
                    "confidence": result.confidence_score,
                    "timestamp": datetime.now().isoformat()
                })

        # Flatten actions
        combined_actions = []
        for action_list in all_actions:
            combined_actions.extend(action_list)

        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.5

        final_response = AgentResponse(
            success=True,
            actions=combined_actions,
            confidence_score=avg_confidence,
            explanation=f"Hierarchical collaboration completed with {len(participants)} agents",
            metadata={
                "collaboration_mode": "hierarchical",
                "master_agent": master_agent.name,
                "slave_agents": len(slave_agents)
            }
        )

        return CollaborationResult(
            success=True,
            final_result=final_response,
            participants=[agent.name for agent in participants],
            confidence_score=avg_confidence,
            audit_trail=audit_trail,
            metadata={"collaboration_strategy": "hierarchical"}
        )

    async def _consensus_mechanism(
        self,
        action_lists: List[List[Any]],
        threshold: float
    ) -> List[Any]:
        """Implement consensus mechanism for combining parallel results."""

        if not action_lists:
            return []

        # Flatten all actions
        all_actions = []
        for action_list in action_lists:
            all_actions.extend(action_list)

        if not all_actions:
            return []

        # Group similar actions
        action_groups = {}
        for action in all_actions:
            key = f"{action.get('action', 'unknown')}:{action.get('payload', {}).get('type', 'unknown')}"
            if key not in action_groups:
                action_groups[key] = []
            action_groups[key].append(action)

        # Select actions with consensus
        consensus_actions = []
        for action_key, actions in action_groups.items():
            if len(actions) == 1:
                # Single action, include it
                consensus_actions.append(actions[0])
            else:
                # Multiple similar actions, check consensus
                confidence_sum = sum(action.get('confidence', 0.5) for action in actions)
                avg_confidence = confidence_sum / len(actions)

                if avg_confidence >= threshold:
                    # High consensus, include the action with highest confidence
                    best_action = max(actions, key=lambda a: a.get('confidence', 0.5))
                    consensus_actions.append(best_action)

        return consensus_actions

    async def get_collaboration_metrics(self) -> Dict[str, Any]:
        """Get comprehensive collaboration metrics."""

        return {
            "active_collaborations": len(self._active_collaborations),
            "collaboration_patterns": list(self._collaboration_patterns.keys()),
            "metrics": {
                "total_collaborations": 0,  # Would be tracked in production
                "average_participants": 0,
                "success_rate": 0.0,
                "average_execution_time": 0.0
            }
        }


# Global collaboration manager instance
_collaboration_manager: Optional[EnterpriseCollaborationManager] = None


def get_collaboration_manager() -> EnterpriseCollaborationManager:
    """Get the global collaboration manager instance."""
    global _collaboration_manager
    if _collaboration_manager is None:
        _collaboration_manager = EnterpriseCollaborationManager()
    return _collaboration_manager


async def initialize_collaboration():
    """Initialize the enterprise collaboration system."""
    global _collaboration_manager

    if _collaboration_manager is None:
        _collaboration_manager = EnterpriseCollaborationManager()
        logger.info("Enterprise Collaboration System initialized")

    return _collaboration_manager


# Example usage function
async def execute_enterprise_collaboration(
    task_description: str,
    available_agents: List[UnifiedAgentInterface],
    tenant_id: str = "default"
) -> CollaborationResult:
    """Execute an enterprise collaboration session."""

    manager = get_collaboration_manager()

    # Create collaboration task
    task = CollaborationTask(
        task_id=f"enterprise_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        description=task_description,
        domain="enterprise",
        complexity="high",
        priority="high",
        required_capabilities={"can_design", "can_analyze", "supports_collaboration"}
    )

    # Execute collaboration
    async with manager.collaboration_session(task, available_agents) as result:
        return result
