# backend/agents/plugin_registry.py
"""Plug‑in registry for OriginFlow agents.

This module maintains a central registry of agent classes and provides
utilities for discovering plug‑ins.  At startup, use :func:`load_plugins`
to import modules from :mod:`backend.plugins` (or another package) so they
can register their agent classes.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import Dict, List, Optional, Type

from backend.agents.base import AgentBase


class PluginRegistry:
    """Registry for agent classes provided by plug‑ins."""

    _registry: Dict[str, Type[AgentBase]] = {}

    @classmethod
    def register(cls, agent_cls: Type[AgentBase]) -> None:
        """Register an agent class.

        Args:
            agent_cls: Class inheriting from :class:`AgentBase`.
        """

        if not issubclass(agent_cls, AgentBase):
            raise TypeError(f"Cannot register non-AgentBase subclass: {agent_cls}")
        name = getattr(agent_cls, "name", None)
        if not name:
            raise ValueError(
                f"Agent class {agent_cls.__name__} must define a 'name' attribute"
            )
        cls._registry[name] = agent_cls

    @classmethod
    def get(cls, name: str) -> Optional[Type[AgentBase]]:
        """Return the registered agent class for ``name`` if present."""

        return cls._registry.get(name)

    @classmethod
    def all(cls) -> List[Type[AgentBase]]:
        """Return all registered agent classes."""

        return list(cls._registry.values())


def load_plugins(package_name: str = "backend.plugins") -> None:
    """Import all modules in ``package_name`` for side-effect registration."""

    try:
        package = importlib.import_module(package_name)
    except ImportError:
        return

    for _, module_name, _ in pkgutil.iter_modules(
        package.__path__, package.__name__ + "."
    ):
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).warning(
                "Failed to import plug-in module %s: %s", module_name, exc
            )


# Provide backward-compatible alias
AgentRegistry = PluginRegistry

