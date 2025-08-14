"""Adapter for the solar domain pack.

This module exposes helper functions to load and return the contents
of the solar domain pack.  Domain packs bundle together formulas,
constraints, component data and other domain-specific knowledge in a
versioned manner.  Clients should call these functions rather than
reading files directly to ensure consistent handling of paths and
formats.
"""
from __future__ import annotations

import os
from typing import Any, Dict

import yaml  # type: ignore


def _get_pack_root() -> str:
    """Return the absolute path to this pack's directory."""
    return os.path.dirname(__file__)


def get_formulas() -> str:
    """Return the raw contents of the formulas markdown file."""
    path = os.path.join(_get_pack_root(), "formulas.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_constraints() -> Dict[str, Any]:
    """Return the constraints defined for this pack.

    The constraints are loaded from ``constraints.yaml`` and returned
    as a dictionary.  Each constraint includes an ID, description,
    check expression and severity.
    """
    path = os.path.join(_get_pack_root(), "constraints.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_components() -> Dict[str, Any]:
    """Return the component catalog for this pack.

    The catalog is loaded from ``components.yaml`` and includes lists
    of panels and inverters with their technical specifications and
    pricing.
    """
    path = os.path.join(_get_pack_root(), "components.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_pack() -> Dict[str, Any]:
    """Return a dictionary aggregating all parts of the pack.

    This helper simplifies loading the formulas, constraints and
    components in one call.
    """
    return {
        "formulas": get_formulas(),
        "constraints": get_constraints(),
        "components": get_components(),
    }
