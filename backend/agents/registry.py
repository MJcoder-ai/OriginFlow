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
