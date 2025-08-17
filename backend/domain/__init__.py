"""Domain pack loading utilities.

The ``backend.domain`` package provides facilities for loading
versioned domain packs and exposing their contents to the
orchestrator and agent templates.  Domain packs reside in the
top-level ``domain_packs`` directory and are organised by domain and
version (e.g. ``domain_packs/solar/v1``).
"""

from .domain_pack_loader import load_domain_pack, available_packs  # noqa: F401
from .domain_rules import (  # noqa: F401
    DOMAIN_CATEGORIES,
    missing_required_categories,
    count_components_by_type,
)

__all__ = [
    "load_domain_pack",
    "available_packs",
    "DOMAIN_CATEGORIES",
    "missing_required_categories",
    "count_components_by_type",
]
