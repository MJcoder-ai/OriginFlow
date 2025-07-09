# backend/agents/registry.py
"""Simple in-memory registry for agents."""
from __future__ import annotations

from typing import Dict, List

from backend.agents.base import AgentBase


_agents: Dict[str, AgentBase] = {}


def register(agent: AgentBase) -> AgentBase:
    """Register an agent instance and return it for decorator use."""

    _agents[agent.name] = agent
    return agent


def get_agent(name: str) -> AgentBase:
    """Retrieve a registered agent by name."""

    return _agents[name]


def get_agent_names() -> List[str]:
    """Return the list of registered agent names."""

    return list(_agents.keys())
