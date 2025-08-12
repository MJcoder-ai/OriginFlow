# backend/auth/dependencies.py
"""Authentication dependencies for route protection."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.auth.auth import current_active_user, current_superuser
from backend.auth.models import User

# Security scheme
security = HTTPBearer()


# Permission decorators
def require_permission(permission: str):
    """Decorator to require specific permission."""
    def permission_checker(
        current_user: Annotated[User, Depends(current_active_user)]
    ):
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return current_user
    return permission_checker


def require_role(role: str):
    """Decorator to require specific role."""
    def role_checker(
        current_user: Annotated[User, Depends(current_active_user)]
    ):
        if current_user.role != role and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {role}"
            )
        return current_user
    return role_checker


# Common permission dependencies
require_ai_access = require_permission("ai.execute")
require_admin_access = require_permission("admin.access")
require_file_upload = require_permission("files.upload")
require_component_manage = require_permission("components.manage")

# Role dependencies
require_admin_role = require_role("admin")
require_user_role = require_role("user")

# Convenience dependencies
AdminUser = Annotated[User, Depends(current_superuser)]
AuthenticatedUser = Annotated[User, Depends(current_active_user)]
AIUser = Annotated[User, Depends(require_ai_access)]
AdminRoleUser = Annotated[User, Depends(require_admin_role)]
