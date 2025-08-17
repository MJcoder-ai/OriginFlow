# backend/services/component_naming_policy.py
"""Utilities for retrieving the active component naming policy.

This module exposes a helper for obtaining the template and version used
to generate human-friendly component names from datasheet metadata. By
centralising this logic in one place, future changes to naming
conventions can be handled via configuration rather than code edits
throughout the project.
"""

from __future__ import annotations

from typing import TypedDict

from backend.config import settings


class NamingPolicy(TypedDict):
    """Structure of the naming policy returned by :func:`get_naming_policy`."""

    template: str
    version: int


def get_naming_policy() -> NamingPolicy:
    """Return the currently active component naming policy.

    The returned dictionary includes the template string used to format
    component names and a version integer to track policy revisions.

    Returns:
        NamingPolicy: current naming template and version.
    """

    return {
        "template": settings.component_name_template,
        "version": settings.component_naming_version,
    }

