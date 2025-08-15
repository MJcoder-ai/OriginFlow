"""Basic meta-cognition planning utilities.

This module provides a simple ``plan_strategy`` helper that infers the
appropriate domain pack and version from a raw user command.  It starts with
the default ``solar`` domain and detects explicit domain names.  If no explicit
match is found, synonyms are inspected: HVAC keywords such as ``"ac"``,
``"air conditioning"``, ``"heat pump"`` or ``"split"`` map to the ``hvac``
domain, while ``"battery"``, ``"storage"``, ``"energy storage"`` and related
terms like ``"ess"`` or ``"bess"`` map to the ``battery`` domain.  When a
detected domain is unavailable, the planner falls back to the default solar
domain.  Version tags of the form ``v2`` or ``v3`` are honoured if present and
available.
"""
from __future__ import annotations

import re
from typing import Dict, List


def plan_strategy(command: str, available: Dict[str, List[str]]) -> Dict[str, str]:
    """Plan a meta-cognition strategy based on the user command.

    The planner selects a domain pack and version by inspecting the command
    string.  Explicit domain names take precedence.  If none are present, the
    command is scanned for HVAC and battery synonyms such as "ac", "air
    conditioning", "heat pump", "split", "ess" or "bess".  Unavailable domains
    trigger a fallback to the default solar domain.

    Args:
        command: Raw user command text.
        available: Mapping of available domain names to lists of versions.

    Returns:
        A dictionary containing ``strategy``, ``domain`` and ``version`` keys.
    """
    cmd_lower = command.lower()

    # 1. Domain selection: choose a domain if its name appears in the
    # command.  Initialise with the default domain "solar" and version "v1".
    # Explicit domain names take precedence; if none are present, detect
    # HVAC and battery synonyms and assign those domains if available.
    domain = "solar"
    version = "v1"
    # First, check explicit domain names present in the command
    for d in available:
        if d and d in cmd_lower:
            domain = d
            break
    # If no explicit domain matched, detect synonyms for HVAC and battery
    if domain == "solar":
        # HVAC synonyms.  Include variations of air conditioning, heat
        # pumps and splits; leading/trailing spaces are used to avoid
        # partial matches within other words.  Synonyms such as
        # "air conditioning" and abbreviations like "ac" or "hvac"
        # trigger the HVAC domain.
        hvac_syns = [
            "hvac", " ac ", " ac", "ac ", "air conditioning", "air conditioner",
            "heat pump", "split", "aircon", "cooling"
        ]
        for syn in hvac_syns:
            if syn in cmd_lower and "hvac" in available:
                domain = "hvac"
                break
        # Battery synonyms.  Include common terms for energy storage
        # systems such as ESS/BESS and generic storage phrases.  These
        # synonyms trigger the battery domain if available.
        if domain == "solar":
            battery_syns = [
                "battery", "storage", "energy storage", "battery system",
                "ess", "bess", "storage system"
            ]
            for syn in battery_syns:
                if syn in cmd_lower and "battery" in available:
                    domain = "battery"
                    break
    # Validate domain availability; fallback to solar if the detected domain is unavailable
    if domain not in available:
        domain = "solar"
    # Detect version suffix like "v2" or "v3".
    vm = re.search(r"v(\d+)", cmd_lower)
    if vm and domain in available and f"v{vm.group(1)}" in available.get(domain, []):
        version = f"v{vm.group(1)}"

    return {"strategy": "naive", "domain": domain, "version": version}
