# backend/agents/__init__.py
"""Package for AI agents used by the OriginFlow backend.

Importing agent classes here triggers their registration with the in-memory
registry and exposes them for convenience. This file ensures new agents are
automatically available when the backend starts.
"""

# Existing agents are imported implicitly elsewhere.

# Import new phase‑1 agents so they register themselves with the registry.
from .inventory_agent import InventoryAgent  # noqa: F401
from .datasheet_fetch_agent import DatasheetFetchAgent  # noqa: F401
from .system_design_agent import SystemDesignAgent  # noqa: F401
from .design_assembly_agent import DesignAssemblyAgent  # noqa: F401
from .wiring_agent import WiringAgent  # noqa: F401
from .performance_agent import PerformanceAgent  # noqa: F401
from .financial_agent import FinancialAgent  # noqa: F401
from .cross_layer_validation_agent import CrossLayerValidationAgent  # noqa: F401
from .sourcing_agent import SourcingAgent  # noqa: F401
from .knowledge_management_agent import KnowledgeManagementAgent  # noqa: F401
from .component_agent import ComponentAgent  # noqa: F401
from .link_agent import LinkAgent  # noqa: F401
from .layout_agent import LayoutAgent  # noqa: F401
from .auditor_agent import AuditorAgent  # noqa: F401
from .bom_agent import BomAgent  # noqa: F401
from .battery_agent import BatteryAgent  # noqa: F401
from .monitoring_agent import MonitoringAgent  # noqa: F401
from .meta_cognition_agent import MetaCognitionAgent  # noqa: F401
from .consensus_agent import ConsensusAgent  # noqa: F401

__all__ = [
    "InventoryAgent",
    "DatasheetFetchAgent",
    "SystemDesignAgent",
    "DesignAssemblyAgent",
    "WiringAgent",
    "PerformanceAgent",
    "FinancialAgent",
    "CrossLayerValidationAgent",
    "SourcingAgent",
    "KnowledgeManagementAgent",
    "ComponentAgent",
    "LinkAgent",
    "LayoutAgent",
    "AuditorAgent",
    "BomAgent",
    "BatteryAgent",
    "MonitoringAgent",
    "MetaCognitionAgent",
    "ConsensusAgent",
]

