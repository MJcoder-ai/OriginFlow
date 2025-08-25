"""Service package init with lazy loading.

This avoids importing optional heavy dependencies (e.g., networkx) at
package import time. Submodules are loaded on first attribute access.
"""
from __future__ import annotations

import importlib
from typing import Any

__all__ = ["odl_graph_service", "ai", "attribute_catalog_service"]


def __getattr__(name: str) -> Any:  # pragma: no cover - thin wrapper
    if name in __all__:
        return importlib.import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__} has no attribute {name}")
