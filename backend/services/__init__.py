"""Lightweight service package init."""

# Re-export commonly used services for backwards compatibility. Keep imports
# minimal to avoid heavy side effects during test discovery.
from . import odl_graph_service  # noqa: F401

__all__ = ["odl_graph_service"]
