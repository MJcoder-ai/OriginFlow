# backend/agents/registry.py
"""Simple in-memory registry for agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from backend.agents.base import AgentBase


@dataclass
class AgentSpec:
    """Metadata describing an agent's domain and capabilities."""

    name: str
    domain: str
    risk_class: str = "low"  # low|medium|high
    capabilities: List[str] = field(default_factory=list)
    description: str = ""
    examples: List[str] = field(default_factory=list)


_REGISTRY: Dict[str, AgentBase] = {}
_SPECS: Dict[str, AgentSpec] = {}


def register(agent: AgentBase) -> AgentBase:
    """Register an agent instance and return it for decorator use."""

    _REGISTRY[agent.name] = agent
    return agent


def get_agent(name: str) -> AgentBase:
    """Retrieve a registered agent by name."""

    return _REGISTRY[name]


def get_agent_names() -> List[str]:
    """Return the list of registered agent names."""

    return list(_REGISTRY.keys())


def register_spec(
    name: str,
    domain: str,
    *,
    risk_class: str = "low",
    capabilities: Optional[List[str]] = None,
    description: str = "",
    examples: Optional[List[str]] = None,
) -> AgentSpec:
    """Register metadata describing an agent's capabilities."""

    spec = AgentSpec(
        name=name,
        domain=domain,
        risk_class=risk_class,
        capabilities=capabilities or [],
        description=description,
        examples=examples or [],
    )
    _SPECS[name] = spec
    return spec


def get_spec(name: str) -> AgentSpec:
    """Return the registered specification for ``name``."""

    return _SPECS[name]


# ---------------------------------------------------------------------------
# Task/agent registry for ODL operations
# ---------------------------------------------------------------------------
from backend.agents.odl_domain_agents import PVDesignAgent  # noqa: E402
from backend.agents.structural_agent import StructuralAgent  # noqa: E402
from backend.agents.wiring_agent import WiringAgent  # noqa: E402
from backend.agents.battery_agent import BatteryAgent  # noqa: E402
from backend.agents.monitoring_agent import MonitoringAgent  # noqa: E402
from backend.agents.meta_cognition_agent import MetaCognitionAgent  # noqa: E402
from backend.agents.consensus_agent import ConsensusAgent  # noqa: E402
from backend.agents.network_agent import NetworkAgent  # import network agent for task mapping and specs  # noqa: E402
from backend.agents.site_planning_agent import SitePlanningAgent  # import site planning agent for task mapping and specs  # noqa: E402
from backend.agents.cross_layer_validation_agent import (
    CrossLayerValidationAgent,
)  # noqa: E402
from backend.agents.network_validation_agent import (
    NetworkValidationAgent,
)  # noqa: E402
from backend.schemas.ai import AiActionType  # noqa: E402


class TaskAgentMapping:
    """Definition of a task-agent mapping with metadata."""
    
    def __init__(self, task_id: str, agent_class, description: str, domain: str, prerequisites: List[str] = None):
        self.task_id = task_id
        self.agent_class = agent_class
        self.description = description
        self.domain = domain
        self.prerequisites = prerequisites or []
        self.agent_instance = None
    
    def get_agent(self):
        """Get or create agent instance (singleton pattern)."""
        if self.agent_instance is None:
            self.agent_instance = self.agent_class()
        return self.agent_instance


class AgentRegistry:
    """
    Enhanced registry mapping task IDs to agent instances with metadata.
    
    This registry enables dynamic planning by providing:
    - Task-to-agent mappings with descriptions
    - Domain categorization for agents
    - Prerequisites tracking for dependency analysis
    - Extensible registration system for new agents
    """

    def __init__(self) -> None:
        self._task_mappings: Dict[str, TaskAgentMapping] = {}
        self._initialize_default_mappings()

    def _initialize_default_mappings(self) -> None:
        """Initialize the default task-agent mappings."""
        # Map task identifiers to agent classes. When adding new domain agents,
        # ensure the tasks are registered here and the corresponding agents are
        # imported above. This mapping drives the planner to dispatch tasks to
        # the correct agent implementations.
        mappings = [
            TaskAgentMapping(
                task_id="meta_cognition",
                agent_class=MetaCognitionAgent,
                description="Generate clarifying questions for blocked tasks",
                domain="meta",
                prerequisites=[],
            ),
            TaskAgentMapping(
                task_id="consensus",
                agent_class=ConsensusAgent,
                description="Select a consensus design among candidate outputs",
                domain="coordination",
                prerequisites=[],
            ),
            TaskAgentMapping(
                task_id="gather_requirements",
                agent_class=PVDesignAgent,
                description="Collect user requirements and verify component availability",
                domain="requirements",
                prerequisites=[],
            ),
            TaskAgentMapping(
                task_id="generate_design",
                agent_class=PVDesignAgent,
                description="Generate preliminary PV system design with panels and inverters",
                domain="electrical",
                prerequisites=["gather_requirements"],
            ),
            TaskAgentMapping(
                task_id="generate_structural",
                agent_class=StructuralAgent,
                description="Generate mounting hardware and structural components",
                domain="structural",
                prerequisites=["generate_design"],
            ),
            TaskAgentMapping(
                task_id="generate_wiring",
                agent_class=WiringAgent,
                description="Generate electrical wiring and protective devices",
                domain="electrical",
                prerequisites=["generate_design"],
            ),
            TaskAgentMapping(
                task_id="generate_battery",
                agent_class=BatteryAgent,
                description="Generate battery storage design",
                domain="battery",
                prerequisites=["generate_design"],
            ),
            TaskAgentMapping(
                task_id="generate_monitoring",
                agent_class=MonitoringAgent,
                description="Generate system monitoring design",
                domain="monitoring",
                prerequisites=["generate_design"],
            ),
            TaskAgentMapping(
                task_id="generate_network",
                agent_class=NetworkAgent,
                description="Generate network topology and communication links",
                domain="network",
                prerequisites=["generate_design"],
            ),
            TaskAgentMapping(
                task_id="generate_site",
                agent_class=SitePlanningAgent,
                description="Generate site layout and planning considerations",
                domain="site",
                prerequisites=["generate_design"],
            ),
            TaskAgentMapping(
                task_id="validate_design",
                agent_class=CrossLayerValidationAgent,
                description="Validate cross-layer connections and component dependencies",
                domain="validation",
                prerequisites=["generate_design"],
            ),
            TaskAgentMapping(
                task_id="validate_network",
                agent_class=NetworkValidationAgent,
                description="Verify network connectivity for inverters and monitoring devices",
                domain="validation",
                prerequisites=["generate_network", "generate_monitoring"],
            ),
            TaskAgentMapping(
                task_id="refine_validate",
                agent_class=PVDesignAgent,
                description="Refine and validate the complete design",
                domain="validation",
                prerequisites=["generate_design"],
            ),
        ]
        
        for mapping in mappings:
            self._task_mappings[mapping.task_id] = mapping

    def register_task(self, task_id: str, agent_class, description: str, domain: str, prerequisites: List[str] = None) -> None:
        """
        Register a new task-agent mapping.
        
        Args:
            task_id: Unique identifier for the task
            agent_class: Agent class that handles this task
            description: Human-readable description of the task
            domain: Domain category (e.g., 'electrical', 'structural', 'validation')
            prerequisites: List of task IDs that must complete before this task
        """
        mapping = TaskAgentMapping(task_id, agent_class, description, domain, prerequisites)
        self._task_mappings[task_id] = mapping

    def get_agent(self, task_id: str):
        """Return the agent responsible for the given task ID."""
        mapping = self._task_mappings.get(task_id)
        return mapping.get_agent() if mapping else None

    def get_task_info(self, task_id: str) -> Dict[str, str]:
        """Return metadata about a task."""
        mapping = self._task_mappings.get(task_id)
        if not mapping:
            return {}
        
        return {
            "task_id": mapping.task_id,
            "description": mapping.description,
            "domain": mapping.domain,
            "prerequisites": mapping.prerequisites
        }

    def available_tasks(self) -> List[str]:
        """Return a list of registered task IDs."""
        return list(self._task_mappings.keys())
    
    def get_tasks_by_domain(self, domain: str) -> List[str]:
        """Return task IDs for a specific domain."""
        return [
            task_id for task_id, mapping in self._task_mappings.items()
            if mapping.domain == domain
        ]
    
    def get_all_domains(self) -> List[str]:
        """Return all available domains."""
        return list(set(mapping.domain for mapping in self._task_mappings.values()))
    
    def get_dependency_map(self) -> Dict[str, List[str]]:
        """Return a map of task dependencies."""
        return {
            task_id: mapping.prerequisites
            for task_id, mapping in self._task_mappings.items()
        }
    
    def validate_task_sequence(self, task_sequence: List[str]) -> List[str]:
        """
        Validate a task sequence and return any dependency violations.
        
        Args:
            task_sequence: Ordered list of task IDs
            
        Returns:
            List of error messages for dependency violations
        """
        errors = []
        completed_tasks = set()
        
        for task_id in task_sequence:
            mapping = self._task_mappings.get(task_id)
            if not mapping:
                errors.append(f"Unknown task: {task_id}")
                continue
            
            # Check prerequisites
            missing_prereqs = [
                prereq for prereq in mapping.prerequisites
                if prereq not in completed_tasks
            ]
            
            if missing_prereqs:
                errors.append(
                    f"Task '{task_id}' missing prerequisites: {', '.join(missing_prereqs)}"
                )
            
            completed_tasks.add(task_id)
        
        return errors


registry = AgentRegistry()

# Register risk specifications for new domain agents
register_spec(
    name=BatteryAgent.name,
    domain="battery",
    risk_class="medium",
    capabilities=[AiActionType.add_component, AiActionType.add_link],
)
register_spec(
    name=MonitoringAgent.name,
    domain="monitoring",
    risk_class="low",
    capabilities=[AiActionType.add_component, AiActionType.add_link],
)
register_spec(
    name=NetworkAgent.name,
    domain="network",
    risk_class="low",
    capabilities=[AiActionType.add_component, AiActionType.add_link],
)
register_spec(
    name=SitePlanningAgent.name,
    domain="site",
    risk_class="low",
    capabilities=[AiActionType.add_component, AiActionType.add_link],
)
