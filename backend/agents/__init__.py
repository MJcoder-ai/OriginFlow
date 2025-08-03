# backend/agents/__init__.py
"""Package for AI agents used by the OriginFlow backend.

Importing agent modules here triggers their registration via the
``@register`` decorator.  This file ensures new agents are automatically
available when the backend starts.
"""

# Existing agents are imported implicitly elsewhere.

# Import new phase‑1 agents so they register themselves with the registry.
from . import inventory_agent  # noqa: F401
from . import datasheet_fetch_agent  # noqa: F401
from . import system_design_agent  # noqa: F401
from . import wiring_agent  # noqa: F401
from . import performance_agent  # noqa: F401
from . import design_assembly_agent  # noqa: F401
from . import financial_agent  # noqa: F401

