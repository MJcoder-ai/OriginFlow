"""Simple authentication endpoints.

This module exposes a minimal ``/me`` endpoint used by the frontend
to determine the current user's roles and permissions. In a
production system this would be backed by proper authentication and
authorization logic. For the purposes of this upgrade this endpoint
returns a static user object.
"""
from __future__ import annotations

from fastapi import APIRouter


router = APIRouter()


@router.get("/me")
async def read_me() -> dict[str, object]:
    """Return the current user profile with roles and permissions.

    The returned user is static in this implementation. A real
    implementation should derive user identity from authentication
    headers or sessions and load roles and permissions from a database.
    """

    return {
        "id": "user-123",
        "org_id": "org-1",
        "roles": ["Admin"],
        "permissions": [
            "memory:read",
            "memory:delete",
            "trace:read",
            "trace:export",
            "policy:edit",
        ],
    }
