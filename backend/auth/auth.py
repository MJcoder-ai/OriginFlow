# backend/auth/auth.py
"""Authentication setup and configuration."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase

from backend.auth.models import User
from backend.auth.config import auth_config
from backend.auth.database import get_user_db


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """User manager for handling user operations."""
    
    reset_password_token_secret = auth_config.SECRET_KEY
    verification_token_secret = auth_config.SECRET_KEY

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Called after successful user registration."""
        print(f"User {user.id} has registered.")
        
        # Set default permissions for new users
        if not user.permissions:
            user.permissions = auth_config.DEFAULT_USER_PERMISSIONS
            # Note: In a real implementation, you'd update the database here

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
    ):
        """Called after successful login."""
        print(f"User {user.id} logged in.")
        
        # Reset failed login attempts on successful login
        user_db = get_user_db()
        await user_db.reset_failed_login(user.id)

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None,
    ):
        """Called after verification request."""
        print(f"Verification requested for user {user.id}. Token: {token}")

    async def authenticate(
        self,
        credentials: str,
        password: str,
        user_db: SQLAlchemyUserDatabase,
    ) -> Optional[User]:
        """Authenticate user with enhanced security checks."""
        
        # Get user by email
        user = await user_db.get_by_email(credentials)
        if not user:
            return None
        
        # Check if account is locked
        if user.is_locked:
            if user.failed_login_attempts >= auth_config.MAX_LOGIN_ATTEMPTS:
                # In production, check if lockout period has expired
                print(f"Account {user.email} is locked due to too many failed attempts")
                return None
        
        # Verify password
        if not self.password_helper.verify_and_update(password, user.hashed_password)[0]:
            # Increment failed login attempts
            await user_db.increment_failed_login(user.id)
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts + 1 >= auth_config.MAX_LOGIN_ATTEMPTS:
                await user_db.lock_user(user.id)
                print(f"Account {user.email} locked due to {auth_config.MAX_LOGIN_ATTEMPTS} failed login attempts")
            
            return None
        
        # Successful authentication
        await user_db.reset_failed_login(user.id)
        return user


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Dependency to get user manager."""
    yield UserManager(user_db)


# JWT Strategy
def get_jwt_strategy() -> JWTStrategy:
    """Get JWT strategy for authentication."""
    return JWTStrategy(
        secret=auth_config.SECRET_KEY,
        lifetime_seconds=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# Transport
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# Authentication Backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# Dependencies
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
