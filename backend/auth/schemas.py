# backend/auth/schemas.py
"""User schemas for API requests and responses."""
from __future__ import annotations

import uuid
from typing import Optional
from datetime import datetime

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema for reading user data."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    role: str = "user"
    created_at: datetime
    last_login: Optional[datetime] = None
    is_locked: bool = False


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating users."""
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    is_verified: bool = False


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating users."""
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    is_verified: Optional[bool] = None


class UserPermissionUpdate(BaseModel):
    """Schema for updating user permissions."""
    permissions: dict
    
    
class LoginResponse(BaseModel):
    """Response schema for successful login."""
    access_token: str
    token_type: str = "bearer"
    user: UserRead
