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
) -> AgentSpec:
    """Register metadata describing an agent's capabilities."""

    spec = AgentSpec(
        name=name,
        domain=domain,
        risk_class=risk_class,
        capabilities=capabilities or [],
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


class AgentRegistry:
    """Singleton registry mapping task IDs to agent instances."""

    def __init__(self) -> None:
        self._agents: Dict[str, object] = {
            "gather_requirements": PVDesignAgent(),
            "generate_design": PVDesignAgent(),
            "refine_validate": PVDesignAgent(),
            "generate_structural": StructuralAgent(),
            "generate_wiring": WiringAgent(),
        }

    def get_agent(self, task_id: str):
        """Return the agent responsible for the given task ID."""
        return self._agents.get(task_id)

    def available_tasks(self) -> List[str]:
        """Return a list of registered task IDs."""
        return list(self._agents.keys())


registry = AgentRegistry()
