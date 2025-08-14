"""Agent template package.

This package contains abstract and concrete templates used by the
DynamicPromptOrchestratorV2.  Templates wrap the logic for specific
reasoning modes (planning, design, selection, etc.) and expose a
uniform ``run`` interface.  Each template derives from the
``AgentTemplate`` base class defined in ``agent_template.py``.

Initial versions implemented the ``PlannerTemplate`` only.  Subsequent
sprints introduced ``PVDesignTemplate`` and ``ComponentSelectorTemplate``
to demonstrate domain-pack integration and component recommendation.
"""

from .agent_template import AgentTemplate  # noqa: F401
from .planner_template import PlannerTemplate  # noqa: F401
from .pv_design_template import PVDesignTemplate  # noqa: F401
from .component_selector_template import ComponentSelectorTemplate  # noqa: F401

__all__ = [
    "AgentTemplate",
    "PlannerTemplate",
    "PVDesignTemplate",
    "ComponentSelectorTemplate",
]
