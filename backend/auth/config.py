# backend/auth/config.py
"""Authentication configuration."""
from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel


class AuthConfig(BaseModel):
    """Configuration for authentication system."""
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security settings
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 30
    
    # Email verification (optional)
    VERIFY_EMAIL: bool = False
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    
    # OAuth settings (for future implementation)
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GITHUB_CLIENT_ID: Optional[str] = os.getenv("GITHUB_CLIENT_ID")
    
    # Default permissions for new users
    DEFAULT_USER_PERMISSIONS: dict = {
        "granted": [
            "ai.execute",
            "components.read",
            "components.create",
            "files.upload",
            "files.read"
        ]
    }
    
    # Admin permissions
    ADMIN_PERMISSIONS: dict = {
        "granted": [
            "admin.access",
            "users.manage",
            "ai.execute",
            "components.manage",
            "files.manage",
            "system.configure"
        ]
    }


auth_config = AuthConfig()
