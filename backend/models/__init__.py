# backend/models/__init__.py
"""Database models for OriginFlow.

Defines SQLAlchemy declarative base and ORM models.
"""

from sqlalchemy.orm import declarative_base

# ⚠️  All ORM models must inherit from this Base.
Base = declarative_base()


__all__ = ["Base"]
