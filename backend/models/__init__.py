# backend/models/__init__.py
"""Database models for OriginFlow.

Defines SQLAlchemy declarative base and ORM models.
"""

from sqlalchemy.orm import declarative_base

# ⚠️  All ORM models must inherit from this Base.
Base = declarative_base()

# Import models so Alembic can locate table metadata
from .component_master import ComponentMaster  # noqa: F401
from .component import Component  # noqa: F401
from .ai_action_log import AiActionLog  # noqa: F401
from .component_hierarchy import HierarchicalComponent, ComponentDocument  # noqa: F401
from .design_vector import DesignVector  # noqa: F401
from .ai_action_vector import AiActionVector  # noqa: F401
from .memory import Memory  # noqa: F401
from .trace_event import TraceEvent  # noqa: F401

__all__ = [
    "Base",
    "ComponentMaster",
    "Component",
    "AiActionLog",
    "HierarchicalComponent",
    "ComponentDocument",
    "DesignVector",
    "AiActionVector",
    "Memory",
    "TraceEvent",
]
