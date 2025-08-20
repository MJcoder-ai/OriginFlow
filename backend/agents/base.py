# backend/agents/base.py
"""Unified base class for AI agents with enterprise-grade capabilities.

This interface provides a comprehensive foundation for all agents in the OriginFlow
platform, supporting both legacy and modern agent patterns with advanced reasoning,
ODL graph integration, and enterprise features.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging

from backend.utils.retry_manager import retry_manager
from backend.utils.schema_enforcer import validate_envelope
from backend.schemas.ai import AiAction, AiActionType
from backend.services import odl_graph_service
from backend.utils.adpf import wrap_response


@dataclass
class AgentCapabilities:
    """Defines what an agent can do and its operational constraints."""

    # Core capabilities
    can_design: bool = False
    can_analyze: bool = False
    can_validate: bool = False
    can_optimize: bool = False

    # Domain expertise
    domains: List[str] = field(default_factory=list)

    # Risk and performance
    risk_level: str = "low"  # low, medium, high, critical
    max_execution_time: float = 30.0  # seconds
    requires_graph_context: bool = False

    # Enterprise features
    supports_streaming: bool = False
    supports_collaboration: bool = False
    supports_explanation: bool = True


@dataclass
class AgentContext:
    """Context information available to all agents."""

    session_id: str
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None
    design_snapshot: Optional[Dict[str, Any]] = None
    recent_actions: Optional[List[Dict[str, Any]]] = None
    requirements: Optional[Dict[str, Any]] = None

    # Advanced reasoning context
    reasoning_depth: str = "standard"  # basic, standard, advanced, expert
    collaboration_mode: bool = False
    explanation_required: bool = True


@dataclass
class AgentResponse:
    """Standardized response format for all agents."""

    success: bool
    actions: List[AiAction] = field(default_factory=list)
    thought_process: Optional[str] = None
    confidence_score: float = 0.0
    reasoning_chain: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ODL graph integration
    graph_patch: Optional[Dict[str, Any]] = None
    graph_description: Optional[str] = None

    # Error handling
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# Backward compatibility alias
AgentBase = UnifiedAgentInterface

class UnifiedAgentInterface(ABC):
    """Enterprise-grade unified agent interface.

    All agents must implement this interface to ensure consistency,
    advanced reasoning capabilities, and enterprise features.
    """

    # Agent identity
    name: str = ""
    description: str = ""
    version: str = "1.0.0"

    # Capabilities and metadata
    capabilities: AgentCapabilities = field(default_factory=AgentCapabilities)
    supported_actions: List[AiActionType] = field(default_factory=list)

    # Configuration
    logger: logging.Logger = None

    def __post_init__(self):
        if self.logger is None:
            self.logger = logging.getLogger(f"agent.{self.name}")

    @abstractmethod
    async def execute_task(
        self,
        task_id: str,
        context: AgentContext,
        **kwargs: Any
    ) -> AgentResponse:
        """Execute a specific task with full context and reasoning.

        This is the primary execution method for all agents, providing:
        - Full context awareness
        - Advanced reasoning capabilities
        - ODL graph integration
        - Standardized response format
        - Error handling and logging

        Args:
            task_id: Unique identifier for the task to execute
            context: Complete context including session, user, and design info
            **kwargs: Additional task-specific parameters

        Returns:
            AgentResponse: Standardized response with actions and metadata
        """
        pass

    async def explain_action(
        self,
        action: AiAction,
        context: AgentContext
    ) -> str:
        """Provide a detailed explanation of why an action was taken.

        Args:
            action: The action to explain
            context: Current execution context

        Returns:
            Detailed explanation string
        """
        return f"Agent {self.name} executed {action.action} based on design requirements."

    async def validate_context(
        self,
        context: AgentContext
    ) -> List[str]:
        """Validate that the provided context is sufficient for execution.

        Args:
            context: Context to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        if self.capabilities.requires_graph_context and not context.design_snapshot:
            errors.append("Graph context required but not provided")
        return errors

    async def get_capabilities_summary(self) -> Dict[str, Any]:
        """Get a summary of agent capabilities for UI and orchestration."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": {
                "design": self.capabilities.can_design,
                "analyze": self.capabilities.can_analyze,
                "validate": self.capabilities.can_validate,
                "optimize": self.capabilities.can_optimize,
                "domains": self.capabilities.domains,
                "risk_level": self.capabilities.risk_level,
                "streaming": self.capabilities.supports_streaming,
                "collaboration": self.capabilities.supports_collaboration,
                "explanation": self.capabilities.supports_explanation
            },
            "supported_actions": [action.value for action in self.supported_actions]
        }

    async def collaborate_with(
        self,
        other_agents: List['UnifiedAgentInterface'],
        task_id: str,
        context: AgentContext
    ) -> AgentResponse:
        """Collaborate with other agents on a complex task.

        Args:
            other_agents: List of agents to collaborate with
            task_id: Task to collaborate on
            context: Execution context

        Returns:
            Combined response from collaboration
        """
        if not self.capabilities.supports_collaboration:
            return AgentResponse(
                success=False,
                errors=["This agent does not support collaboration"]
            )

        # Default implementation - override in collaborative agents
        responses = []
        for agent in other_agents:
            response = await agent.execute_task(task_id, context)
            responses.append(response)

        # Combine responses
        combined_actions = []
        combined_errors = []

        for response in responses:
            combined_actions.extend(response.actions)
            combined_errors.extend(response.errors)

        return AgentResponse(
            success=len(combined_errors) == 0,
            actions=combined_actions,
            errors=combined_errors,
            metadata={"collaboration": True, "agents_involved": len(responses)}
        )




    # Agent lifecycle methods
    async def initialize(self) -> None:
        """Initialize the agent with any required setup."""
        pass

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        pass
