"""Service package init.

Expose subpackages explicitly to avoid import resolution issues in
non-installed test environments.
"""

# Re-export commonly used services for backwards compatibility. Keep imports
# minimal to avoid heavy side effects during test discovery.
from . import odl_graph_service  # noqa: F401
from . import ai as ai  # noqa: F401

__all__ = ["odl_graph_service", "ai"]
