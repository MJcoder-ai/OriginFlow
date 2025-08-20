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
NETWORK_CUES = {"network", "ethernet", "wifi", "wi-fi", "ssid", "switch", "router", "firewall", "access point", "ap"}
HVAC_CUES    = {"hvac", "pump", "chiller", "boiler"}
PV_CUES      = {"pv", "solar", "module", "panel", "inverter", "battery", "string", "combiner"}

ALL_DOMAINS: Dict[str, List[str]] = {**PV, **HVAC, **NETWORK}


def _phrase_present(text: str, phrase: str) -> bool:
    """
    Return True if `phrase` appears as a standalone phrase/token in `text`.
    - Multi-word or hyphenated phrases get non-word guards: (?<!\\w) ... (?!\\w)
    - Single tokens use word boundaries: \\b...\\b
    """
    p = phrase.lower()
    if " " in p or "-" in p:
        pattern = r"(?<!\w)" + re.escape(p) + r"(?!\w)"
    else:
        pattern = r"\b" + re.escape(p) + r"\b"
    return re.search(pattern, text) is not None


def _collect_candidates(text: str, domain: Dict[str, List[str]]) -> List[Tuple[str, int]]:
    """Return [(canonical, score)] from exact + fuzzy matches in a single domain."""
    scores: List[Tuple[str, int]] = []
    t = text.lower()
    # Exact phrase priority (esp. bigrams like "access point")
    for canon, names in domain.items():
        for name in names:
            if _phrase_present(t, name):
                scores.append((canon, 100))
                break
    # Fuzzy (single-token typos) — tune so "pupm" -> "pump" passes.
    THRESH = 0.69
    tokens = re.findall(r"[a-zA-Z0-9\-]+", t)
    for token in tokens:
        for canon, names in domain.items():
            # Compare token against each alias; if any alias is close enough, accept.
            match = get_close_matches(token, [n.lower() for n in names], n=1, cutoff=THRESH)
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
    # Ambiguity: close scores (<=5) OR multiple explicit 100s
    if ordered[0][1] == 100 and len([v for v in agg.values() if v == 100]) >= 2:
        return None
    if ordered[0][1] - ordered[1][1] <= 5:
        return None
    return ordered[0][0]


def resolve_canonical_class(text: str) -> Optional[str]:
    """
    Lightweight, deterministic resolver used by the intent firewall.
    Returns a canonical class string (e.g. 'panel', 'inverter', 'ap') or None if ambiguous.
    """
    t = text.lower()
    # Detect domain with phrase-aware cues; if none triggered, search all domains.
    domain_selected = False
    domain_map: Dict[str, List[str]] = ALL_DOMAINS
    if any(_phrase_present(t, cue) for cue in NETWORK_CUES):
        domain_map = NETWORK
        domain_selected = True
    elif any(_phrase_present(t, cue) for cue in HVAC_CUES):
        domain_map = HVAC
        domain_selected = True
    elif any(_phrase_present(t, cue) for cue in PV_CUES):
        domain_map = PV
        domain_selected = True

    # Candidates within selected domain; fallback to global if nothing found.
    scores = _collect_candidates(t, domain_map)
    if domain_selected and not scores:
        scores = _collect_candidates(t, ALL_DOMAINS)
    choice = _decide(scores)
    return choice
