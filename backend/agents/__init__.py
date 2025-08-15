# backend/agents/__init__.py
"""Package for AI agents used by the OriginFlow backend.

Importing agent modules here triggers their registration with the in-memory
registry.  This file ensures new agents are automatically available when the
backend starts.
"""

# Existing agents are imported implicitly elsewhere.

# Import new phase‑1 agents so they register themselves with the registry.
from . import inventory_agent  # noqa: F401
from . import datasheet_fetch_agent  # noqa: F401
from . import system_design_agent  # noqa: F401
from . import design_assembly_agent  # noqa: F401
from . import wiring_agent  # noqa: F401
from . import performance_agent  # noqa: F401
from . import financial_agent  # noqa: F401
from . import cross_layer_validation_agent  # noqa: F401
from . import sourcing_agent  # noqa: F401
from . import knowledge_management_agent  # noqa: F401
from . import component_agent  # noqa: F401
from . import link_agent  # noqa: F401
from . import layout_agent  # noqa: F401
from . import auditor_agent  # noqa: F401
from . import bom_agent  # noqa: F401
from . import battery_agent  # noqa: F401
from . import monitoring_agent  # noqa: F401

