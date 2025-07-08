# backend/models/__init__.py
"""Database models for OriginFlow.

Defines SQLAlchemy declarative base and ORM models.
"""

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all ORM models."""

__all__ = ["Base"]
