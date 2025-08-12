# backend/auth/models.py
"""User authentication models."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.models import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User model extending FastAPI Users base."""
    
    __tablename__ = "users"

    # Core user fields
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    organization: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Authentication and authorization
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    
    # Permissions and capabilities
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Audit fields
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Account status
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"

    @property
    def display_name(self) -> str:
        """Return the user's display name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_superuser:
            return True
        
        if not self.permissions:
            return False
            
        return permission in self.permissions.get("granted", [])

    def can_access_route(self, route: str) -> bool:
        """Check if user can access a specific route."""
        # Define route-based permissions
        route_permissions = {
            "/api/v1/admin/": ["admin.access"],
            "/api/v1/ai/": ["ai.execute"],
            "/api/v1/files/upload": ["files.upload"],
            "/api/v1/components/": ["components.manage"],
        }
        
        for route_pattern, required_perms in route_permissions.items():
            if route.startswith(route_pattern):
                return any(self.has_permission(perm) for perm in required_perms)
        
        # Default allow for authenticated users
        return True
