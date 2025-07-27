# backend/models/__init__.py
"""Database models for OriginFlow.

Defines SQLAlchemy declarative base and ORM models.
"""

from sqlalchemy.orm import declarative_base

# ⚠️  All ORM models must inherit from this Base.
Base = declarative_base()

# Import models so Alembic can locate table metadata
from .component_master import ComponentMaster  # noqa: F401


__all__ = ["Base", "ComponentMaster"]
