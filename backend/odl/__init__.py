"""ODL graph service stubs.

This package provides a lightweight, in-memory implementation of the
OriginFlow ODL graph service used to persist context contracts and
patches.  In the production system the ODL service would manage a
graph database of design sessions, including system topology and
associated contracts.  During the ADPF 2.1 migration we introduce
these stubs to persist contracts and aggregate patches on disk and in
memory, enabling session continuity and auditability without requiring
a full graph database.
"""

from .graph_service import get_contract, save_contract, add_patch, get_patches

__all__ = ["get_contract", "save_contract", "add_patch", "get_patches"]

