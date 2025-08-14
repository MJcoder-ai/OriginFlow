"""Utility for loading versioned domain packs.

Domain packs are organised under the top-level ``domain_packs``
directory by domain name and version.  For example, the solar pack
version 1 lives at ``domain_packs/solar/v1`` and exposes an
``adapter`` module with helper functions.  This loader dynamically
imports the adapter and returns its aggregated contents via the
``load_pack`` function.

Example usage:

```
from backend.domain import load_domain_pack

pack = load_domain_pack("solar", "v1")
formulas = pack["formulas"]
constraints = pack["constraints"]
components = pack["components"]
```
"""
from __future__ import annotations

import importlib
from typing import Any, Dict


def load_domain_pack(domain: str, version: str = "v1") -> Dict[str, Any]:
    """Dynamically load the specified domain pack.

    Args:
        domain: The name of the domain (e.g. "solar").
        version: The version identifier (e.g. "v1").  Defaults to
            ``"v1"``.

    Returns:
        A dictionary with keys ``formulas``, ``constraints`` and
        ``components`` containing the domain knowledge.

    Raises:
        ImportError: If the specified pack cannot be imported.
        AttributeError: If the imported module does not expose
            ``load_pack``.
    """
    module_name = f"domain_packs.{domain}.{version}.adapter"
    adapter_module = importlib.import_module(module_name)
    if not hasattr(adapter_module, "load_pack"):
        raise AttributeError(
            f"Domain pack adapter '{module_name}' does not define 'load_pack'"
        )
    return adapter_module.load_pack()
