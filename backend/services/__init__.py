"""
Service package initialisation for OriginFlow.

This module exports commonly used services at the package level to
simplify imports in other parts of the codebase.  For example:

    from backend.services import PlannerOrchestrator, get_placeholder_catalog

When adding new services, import them here so that consumers can
reference them via the package root.  See individual service modules
for detailed documentation.
"""

from .orchestrator import PlannerOrchestrator  # noqa: F401
from .placeholder_components import get_placeholder_catalog  # noqa: F401
from .workflow_engine import WorkflowEngine, SagaStep  # noqa: F401

__all__ = [
    "PlannerOrchestrator",
    "get_placeholder_catalog",
    "WorkflowEngine",
    "SagaStep",
]

