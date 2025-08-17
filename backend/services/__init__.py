"""
Service package initialisation for OriginFlow.

This module exports commonly used services at the package level to
simplify imports in other parts of the codebase.  For example:

    from backend.services import PlannerOrchestrator, get_placeholder_catalog

When adding new services, import them here so that consumers can
reference them via the package root.  See individual service modules
for detailed documentation.
"""

from .component_naming_service import ComponentNamingService  # noqa: F401
from .orchestrator import PlannerOrchestrator  # noqa: F401
from .placeholder_components import get_placeholder_catalog  # noqa: F401
from .calculation_engines import (  # noqa: F401
    BaseCalculationEngine,
    PVCalculationEngine,
    HVACCalculationEngine,
    WaterCalculationEngine,
)
from .workflow_engine import WorkflowEngine, SagaStep  # noqa: F401
from .snapshot_service import SnapshotService  # noqa: F401

__all__ = [
    "PlannerOrchestrator",
    "get_placeholder_catalog",
    "ComponentNamingService",
    "WorkflowEngine",
    "SagaStep",
    "BaseCalculationEngine",
    "PVCalculationEngine",
    "HVACCalculationEngine",
    "WaterCalculationEngine",
    "SnapshotService",
]
