from __future__ import annotations
"""
Intent firewall for domain-aware, fuzzy, and ambiguity-safe component classification.

Why:
- `action_guard.py` and `ai_service.py` import `resolve_canonical_class` but this module
  didn't exist in the new tree, breaking imports during test collection.
- We provide domain-aware classification that handles typos, multi-entity ambiguity,
  and explicit intent detection.
"""
from typing import Optional, Dict, List, Tuple
import re
from difflib import get_close_matches


# Canonical classes by domain with rich synonyms.
PV: Dict[str, List[str]] = {
    "panel":    ["panel", "module", "pv panel", "pv module", "solar panel", "panell", "panels"],
    "inverter": ["inverter", "invertor", "inverter charger"],
    "battery":  ["battery", "batt", "battary", "ess", "energy storage"],
    "combiner": ["combiner", "combiner box"],
}

HVAC: Dict[str, List[str]] = {
    "pump": ["pump", "circulation pump", "circulator", "coolant pump"],
}

NETWORK: Dict[str, List[str]] = {
    "router":  ["router", "l3 router"],
    "switch":  ["switch", "network switch", "l2 switch"],
    "firewall":["firewall", "ngfw"],
    "ap":      ["access point", "wireless access point", "wifi ap", "wi-fi ap", "ap"],
}

# Quick domain cues (any hit enables domain-restricted matching)
NETWORK_CUES = {"network", "ethernet", "wifi", "wi-fi", "ssid", "switch", "router", "firewall", "access point", "ap "}
HVAC_CUES    = {"hvac", "pump", "chiller", "boiler"}
PV_CUES      = {"pv", "solar", "module", "panel", "inverter", "battery", "string", "combiner"}


def _collect_candidates(text: str, domain: Dict[str, List[str]]) -> List[Tuple[str, int]]:
    """Return [(canonical, score)] from exact + fuzzy matches in a single domain."""
    scores: List[Tuple[str, int]] = []
    t = text.lower()
    # Exact phrase priority (especially for bigrams like "access point")
    for canon, names in domain.items():
        for name in names:
            if f" {name} " in f" {t} ":
                scores.append((canon, 100))
                break
    # Fuzzy (single-token typos)
    # Use conservative threshold 72 so "pupm" -> "pump" passes.
    THRESH = 72
    tokens = re.findall(r"[a-zA-Z0-9\-]+", t)
    for token in tokens:
        for canon, names in domain.items():
            match = get_close_matches(token, names, n=1, cutoff=THRESH/100.0)
            if match:
                scores.append((canon, 80))  # fuzzy weight
    return scores


def _decide(scores: List[Tuple[str, int]]) -> Optional[str]:
    """Pick best class, but return None when ambiguous."""
    if not scores:
        return None
    # Aggregate by canonical
    agg: Dict[str, int] = {}
    for canon, sc in scores:
        agg[canon] = max(agg.get(canon, 0), sc)
    # Sort by score
    ordered = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
    if len(ordered) == 1:
        return ordered[0][0]
    # Ambiguity: close scores (within 5) OR multiple explicit entities
    if ordered[0][1] - ordered[1][1] <= 5:
        return None
    return ordered[0][0]


def resolve_canonical_class(text: str) -> Optional[str]:
    """
    Domain-aware canonical class resolver.
    - Prioritizes domain cues to restrict matching.
    - Exact phrase ('access point') outranks abbreviations ('ap').
    - Fuzzy matching tolerates common typos ('pupm' → 'pump').
    - Returns None when multiple classes are referenced ('inverter and panel').
    """
    t = (text or "").lower().strip()
    if not t:
        return None

    # Multi-entity guard – if obvious conjunctions join known items, mark ambiguous
    if re.search(r"\b(and|,|/)\b", t) and any(k in t for k in ("inverter", "panel", "battery", "router", "switch", "firewall", "access point", "ap ", "pump")):
        # Let scoring still run; if it detects near-tie, return None.
        pass

    # Detect domain
    domain_map = PV | HVAC | NETWORK  # fallback to "all"
    if any(cue in t for cue in NETWORK_CUES):
        domain_map = NETWORK
    elif any(cue in t for cue in HVAC_CUES):
        domain_map = HVAC
    elif any(cue in t for cue in PV_CUES):
        domain_map = PV

    # Candidates within selected domain; if domain was not detected, try all and rely on ambiguity guard.
    scores = _collect_candidates(t, domain_map)
    if domain_map is not (PV | HVAC | NETWORK):
        # Domain was detected; great. If no matches (rare), try global as fallback.
        if not scores:
            scores = _collect_candidates(t, PV | HVAC | NETWORK)
    choice = _decide(scores)
    return choice
