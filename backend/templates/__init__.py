"""Agent template package.

This package contains abstract and concrete templates used by the
DynamicPromptOrchestratorV2.  Templates wrap the logic for specific
reasoning modes (planning, design, selection, etc.) and expose a
uniform ``run`` interface.  Each template derives from the
``AgentTemplate`` base class defined in ``agent_template.py``.

During Sprint 1–2 only the ``PlannerTemplate`` is implemented.  It
provides a thin wrapper around the legacy planning logic and returns
results in a standard structure.  Future sprints will add
implementations for PV design, component selection, wiring, structural
design and others.
"""

from .agent_template import AgentTemplate  # noqa: F401
from .planner_template import PlannerTemplate  # noqa: F401

__all__ = ["AgentTemplate", "PlannerTemplate"]
