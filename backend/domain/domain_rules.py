"""Domain requirement definitions and validation utilities.

This module defines the categories of components required or
recommended for each supported domain (e.g. PV, HVAC, water
pumping).  It also provides helper functions to validate that a
design snapshot contains all mandatory categories for the target
domain.

The domain categories defined here are intended to guide the AI
planning and validation services.  When a user designs a system for
``pv`` (solar photovoltaics), at minimum a panel and an inverter
must be present; other categories such as batteries are optional.
For ``hvac`` and ``water`` domains, similar mappings are provided.

These mappings should be kept in sync with the component library
taxonomy and can be expanded as new domains or categories are
introduced.
"""

from __future__ import annotations

from typing import Dict, List

from backend.schemas.analysis import DesignSnapshot

# Define required and optional component categories for each domain.
# Category names correspond to the ``type`` attribute on components
# (e.g. a panel component has type "panel").  Optional categories
# may enhance performance or safety but are not strictly required.
DOMAIN_CATEGORIES: Dict[str, Dict[str, List[str]]] = {
    "pv": {
        # A PV system must at least have panels and an inverter
        "required": ["panel", "inverter"],
        # Batteries, chargers and optimisers are optional but common
        "optional": ["battery", "charger", "optimizer", "monitor"],
        # Accessories such as mounts or monitoring equipment
        "accessory": ["mount", "combiner_box"],
    },
    "hvac": {
        # Typical HVAC system components
        "required": ["compressor", "air_handler"],
        "optional": ["condenser", "evaporator", "thermostat"],
        "accessory": ["filter", "humidifier"],
    },
    "water": {
        # Water pumping system components
        "required": ["pump", "controller"],
        "optional": ["tank", "sensor"],
        "accessory": ["valve", "filter"],
    },
}


def missing_required_categories(
    snapshot: DesignSnapshot, domain: str
) -> List[str]:
    """Return a list of required categories missing from the snapshot.

    Args:
        snapshot: The design snapshot containing components.
        domain: The domain key (e.g. "pv").

    Returns:
        A list of category names that are required but not present in
        the snapshot.  If the domain is unknown, an empty list is
        returned.
    """
    categories = DOMAIN_CATEGORIES.get(domain)
    if not categories:
        return []
    required = categories.get("required", [])
    present_types = {comp.type for comp in snapshot.components}
    missing = [cat for cat in required if cat not in present_types]
    return missing


def count_components_by_type(snapshot: DesignSnapshot) -> Dict[str, int]:
    """Return a mapping from component type to its count in the snapshot.

    Args:
        snapshot: The design snapshot containing components.

    Returns:
        A dictionary mapping component types (``str``) to counts (``int``).
    """
    counts: Dict[str, int] = {}
    for comp in snapshot.components:
        counts[comp.type] = counts.get(comp.type, 0) + 1
    return counts
