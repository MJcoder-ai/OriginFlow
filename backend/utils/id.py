# backend/utils/id.py
"""ID generation utilities.

Provides helper functions for generating unique identifiers.
"""
from __future__ import annotations

import uuid


def generate_id(prefix: str) -> str:
    """Return a unique identifier with the given ``prefix``."""

    return f"{prefix}_{uuid.uuid4()}"
