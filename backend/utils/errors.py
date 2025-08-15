"""
Custom exceptions used throughout the OriginFlow backend.

Having explicit error types makes it easy for orchestrators and higher-level
components to handle failures consistently.  These errors distinguish between
invalid patches, conflicting updates, missing sessions and other unexpected
conditions.
"""

from __future__ import annotations


class OriginFlowError(Exception):
    """Base class for all custom OriginFlow exceptions."""


class InvalidPatchError(OriginFlowError):
    """Raised when an ODLGraphPatch is structurally invalid or inconsistent."""


class DesignConflictError(OriginFlowError):
    """Raised when a graph update conflicts with the current state."""


class SessionNotFoundError(OriginFlowError):
    """Raised when the requested ODL session does not exist."""
