# backend/auth/database.py
"""Database adapter for FastAPI Users."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import func

from backend.database.session import get_session
from backend.auth.models import User


class UserDatabase(SQLAlchemyUserDatabase):
    """Extended user database with additional methods."""
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        statement = select(self.user_table).where(
            func.lower(self.user_table.email) == func.lower(email)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def increment_failed_login(self, user_id: uuid.UUID) -> None:
        """Increment failed login attempts for a user."""
        statement = (
            update(self.user_table)
            .where(self.user_table.id == user_id)
            .values(failed_login_attempts=self.user_table.failed_login_attempts + 1)
        )
        await self.session.execute(statement)
        await self.session.commit()
    
    async def reset_failed_login(self, user_id: uuid.UUID) -> None:
        """Reset failed login attempts for a user."""
        statement = (
            update(self.user_table)
            .where(self.user_table.id == user_id)
            .values(
                failed_login_attempts=0,
                last_login=func.now()
            )
        )
        await self.session.execute(statement)
        await self.session.commit()
    
    async def lock_user(self, user_id: uuid.UUID) -> None:
        """Lock a user account."""
        statement = (
            update(self.user_table)
            .where(self.user_table.id == user_id)
            .values(is_locked=True)
        )
        await self.session.execute(statement)
        await self.session.commit()
    
    async def unlock_user(self, user_id: uuid.UUID) -> None:
        """Unlock a user account."""
        statement = (
            update(self.user_table)
            .where(self.user_table.id == user_id)
            .values(
                is_locked=False,
                failed_login_attempts=0
            )
        )
        await self.session.execute(statement)
        await self.session.commit()


async def get_user_db(session: AsyncSession = Depends(get_session)) -> UserDatabase:
    """Dependency to get user database."""
    yield UserDatabase(session, User)
