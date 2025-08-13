"""In-memory component library service.

This service is a placeholder used by domain agents to query and store
component specifications. It keeps components in a simple list of
 dictionaries keyed by part number. Replace with a real database-backed
implementation when available.
"""
from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional


class ComponentDBService:
    """Lightweight in-memory component store."""

    def __init__(self) -> None:
        self.components: List[Dict[str, Any]] = []

    async def exists(self, category: str) -> bool:
        """Return True if any component of the given category exists."""
        return any(c for c in self.components if c.get("category") == category)

    async def search(self, category: str, min_power: Optional[float] = None) -> List[Dict[str, Any]]:
        """Return components in the given category, optionally filtered by power.

        Args:
            category: Component category to search (e.g., 'panel', 'inverter').
            min_power: Optional minimum power/capacity rating to filter results.
        """
        results = [c for c in self.components if c.get("category") == category]
        if min_power is not None:
            def meets_power(comp: Dict[str, Any]) -> bool:
                value = comp.get("power")
                if value is None:
                    value = comp.get("capacity")
                try:
                    return float(value) >= float(min_power)
                except (TypeError, ValueError):
                    return False
            results = [c for c in results if meets_power(c)]
        return results

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

    async def get_by_part_number(self, part_number: str) -> Optional[Dict[str, Any]]:
        """Return the first component matching ``part_number``.

        The in-memory store keeps components as dictionaries keyed by
        ``part_number``.  This helper searches the list and returns the
        matching component dictionary when found or ``None`` otherwise.
        """

        for comp in self.components:
            if comp.get("part_number") == part_number:
                return comp
        return None


async def get_component_db_service() -> AsyncIterator[ComponentDBService]:
    """FastAPI-style dependency provider yielding a component DB service.

    The current implementation provides an in-memory store per request.
    """
    yield ComponentDBService()
