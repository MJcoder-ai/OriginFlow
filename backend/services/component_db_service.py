"""In-memory component library service.

This service is a placeholder used by domain agents to query and store
component specifications. It keeps components in a simple list of
 dictionaries keyed by part number. Replace with a real database-backed
implementation when available.
"""
from __future__ import annotations

from typing import Any, Dict, List


class ComponentDBService:
    """Lightweight in-memory component store."""

    def __init__(self) -> None:
        self.components: List[Dict[str, Any]] = []

    async def exists(self, category: str) -> bool:
        """Return True if any component of the given category exists."""
        return any(c for c in self.components if c.get("category") == category)

    async def search(self, category: str) -> List[Dict[str, Any]]:
        """Return all components in the given category."""
        return [c for c in self.components if c.get("category") == category]

    async def ingest(
        self, category: str, part_number: str, attributes: Dict[str, Any]
    ) -> str:
        """
        Store or update a component.  Attributes should include 'power' for panels
        and 'capacity' for inverters to support automatic sizing.
        """
        component = {"category": category, "part_number": part_number}
        component.update(attributes)
        for idx, c in enumerate(self.components):
            if c.get("part_number") == part_number:
                self.components[idx] = component
                return part_number
        self.components.append(component)
        return part_number
