from __future__ import annotations
"""
Agent base class used by all OriginFlow agents.

Why this exists:
- The previous refactor aliased `AgentBase = UnifiedAgentInterface` while
  `UnifiedAgentInterface` wasn't defined in this module, causing import-time
  crashes across all agents and tests.
- We restore a minimal, dependency-free ABC that other agents can implement
  without pulling in heavy modules or creating circular imports.
"""
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    # Delayed import to avoid circular dependencies at module import time
    from backend.schemas.analysis import DesignSnapshot


class AgentBase(ABC):
    """
    Minimal enterprise-safe base class for all agents.

    Subclasses must implement `execute_task`. Additional optional hooks
    (setup/teardown) are provided but can be no-ops.
    """

    #: Human-readable identifier
    name: str = "agent"
    #: One-line description of the agent
    description: str = ""
    #: Capability tags used by the orchestrator (e.g. ["design","routing"])
    capability_tags: List[str] = []

    async def setup(self) -> None:  # pragma: no cover - optional
        """Optional async initialization hook."""
        return None

    async def teardown(self) -> None:  # pragma: no cover - optional
        """Optional async teardown hook."""
        return None

    async def execute_task(
        self,
        task: Dict[str, Any],
        snapshot: Optional["DesignSnapshot"] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Execute a single task and return a list of normalized actions.
        Each action is a dict shaped for `/ai/apply` (server firewall will
        revalidate).

        Default implementation returns empty list. Subclasses should override.
        """
        # Default implementation - return empty actions
        return []