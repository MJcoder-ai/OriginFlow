"""In-memory component library service.

This module provides a very small in-memory component database.  Agents use
it during tests to look up mock components without requiring a real database
backend.  The real project will eventually replace this with a proper
database-backed implementation, but for now a lightweight store suffices.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional


class ComponentDBService:
    """Lightweight in-memory component store."""

    def __init__(self) -> None:
        # store components as ``SimpleNamespace`` objects to allow attribute access
        self.components: List[SimpleNamespace] = []

    async def exists(self, category: str) -> bool:
        """Return ``True`` if any component of the given category exists."""
        return any(c for c in self.components if c.category == category)

    async def search(self, category: str, min_power: float | None = None) -> List[SimpleNamespace]:
        """Return all components in ``category`` optionally filtered by ``min_power``.

        The ``min_power`` value is compared against either the ``power`` or
        ``capacity`` attribute of a component, whichever is present. Components
        lacking these attributes are considered to have zero power.
        """

        def meets_power(c: SimpleNamespace) -> bool:
            if min_power is None:
                return True
            power = getattr(c, "power", None)
            capacity = getattr(c, "capacity", None)
            return (power or capacity or 0) >= min_power

        return [c for c in self.components if c.category == category and meets_power(c)]

    async def get_by_part_number(self, part_number: str) -> Optional[SimpleNamespace]:
        """Return the component matching ``part_number`` or ``None``."""
        for c in self.components:
            if c.part_number == part_number:
                return c
        return None

    async def ingest(
        self, category: str, part_number: str, attributes: Dict[str, Any]
    ) -> str:
        """Store or update a component and return its part number.

        Attributes are stored on the resulting ``SimpleNamespace`` so callers can
        access fields using ``component.power`` or ``component.price`` as expected
        by the agents and tests.
        """

        component = SimpleNamespace(category=category, part_number=part_number, **attributes)
        for idx, c in enumerate(self.components):
            if c.part_number == part_number:
                self.components[idx] = component
                return part_number
        self.components.append(component)
        return part_number


_service: ComponentDBService | None = None


@asynccontextmanager
async def get_component_db_service() -> Iterable[ComponentDBService]:
    """Provide a singleton :class:`ComponentDBService` instance.

    The function is implemented as an async context manager so callers can use
    ``async for svc in get_component_db_service():`` which mirrors the pattern
    employed by FastAPI dependency injection.  The service is created on first
    use and reused thereafter.
    """

    global _service
    if _service is None:
        _service = ComponentDBService()
    try:
        yield _service
    finally:
        # No cleanup is necessary for the in-memory implementation
        pass
