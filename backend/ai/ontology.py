from __future__ import annotations
"""
Domain Ontology & Synonyms (enterprise-grade, multi-domain).

Purpose:
- Map natural-language mentions (incl. typos) to canonical component classes
  in multiple domains. Extend this file when you add new domains or classes.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import difflib
import re


def _phrase_present(s: str, phrase: str) -> bool:
    """Return True if *phrase* appears in *s* with word boundaries."""
    p = phrase.lower()
    if " " in p or "-" in p:
        pattern = r"(?<!\w)" + re.escape(p) + r"(?!\w)"
    else:
        pattern = r"\b" + re.escape(p) + r"\b"
    return re.search(pattern, s) is not None


STOP_WORDS = {
    "and",
    "or",
    "the",
    "a",
    "an",
    "to",
    "with",
    "no",
    "in",
    "on",
    "for",
    "of",
    "by",
    "something",
}

# Canonical classes are short, snake-case nouns (match what your backend uses)
# e.g., "panel", "inverter", "battery", "meter", "switch", ...

@dataclass(frozen=True)
class DomainOntology:
    name: str
    # canonical_class -> synonyms
    synonyms: Dict[str, List[str]]

    def detect_explicit(self, text: str) -> Optional[str]:
        """
        Phrase-aware explicit detection.
        Returns the canonical class if exactly one class/synonym is present.
        If multiple classes are mentioned or none are found, returns ``None``.
        """
        t = (text or "").lower()
        hits: List[str] = []
        for clazz, syns in self.synonyms.items():
            all_terms = [clazz, *syns]
            if any(_phrase_present(t, term) for term in all_terms):
                hits.append(clazz)
        uniq = list(dict.fromkeys(hits))
        if len(uniq) == 1:
            return uniq[0]
        return None

    def fuzzy_guess(self, text: str, cutoff: float = 0.70) -> Optional[str]:
        """
        Fuzzy guess with SequenceMatcher; useful for minor typos ("invertor", "battary", etc.).
        Only activates if explicit detect fails.
        """
        t = (text or "").lower()
        lex: List[Tuple[str, str]] = []  # (surface, canonical)
        for clazz, syns in self.synonyms.items():
            lex.append((clazz, clazz))
            for s in syns:
                lex.append((s, clazz))
        surfaces = [s for s, _ in lex]
        best = None
        best_ratio = 0.0
        for token in t.replace("/", " ").replace("-", " ").split():
            if len(token) <= 2 or token in STOP_WORDS:
                continue
            cand = difflib.get_close_matches(token, surfaces, n=1, cutoff=cutoff)
            if cand:
                surface = cand[0]
                if abs(len(token) - len(surface)) > 2:
                    continue
                for s, c in lex:
                    if s == surface:
                        ratio = difflib.SequenceMatcher(a=token, b=surface).ratio()
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best = c
        return best


# ----------------------------
# Example domain ontologies
# ----------------------------

PV_ONTOLOGY = DomainOntology(
    name="pv",
    synonyms={
        "panel": ["pv module", "module", "solar panel", "panelboard"],  # "panelboard" sometimes shows up incorrectly; still maps to panel
        "inverter": ["string inverter", "central inverter", "microinverter", "micro inverter"],
        "battery": ["battery pack", "energy storage", "ess"],
        "meter": ["metering", "kwh meter"],
        "optimizer": ["dc optimizer", "optimizer"],
        "combiner": ["combiner box", "combiner"],
        "disconnect": ["isolator", "dc disconnect", "ac disconnect"],
        "controller": ["charge controller", "mppt controller", "controller"],
    },
)

# Placeholder additional domains (extend as needed)
HVAC_ONTOLOGY = DomainOntology(
    name="hvac",
    synonyms={
        "air_handler": ["ahu", "air handling unit"],
        "chiller": ["chiller"],
        "boiler": ["boiler"],
        "pump": ["circulation pump", "pump"],
        "cooling_tower": ["cooling tower", "ct"],
        "thermostat": ["thermostat", "temp controller"],
    },
)

NETWORK_ONTOLOGY = DomainOntology(
    name="network",
    synonyms={
        "switch": ["switch", "layer2 switch", "l2 switch"],
        "router": ["router", "l3 router", "layer3 router"],
        "firewall": ["firewall"],
        "ap": ["access point", "wifi ap", "ap"],
        "server": ["server", "host"],
    },
)

DEFAULT_DOMAINS = [PV_ONTOLOGY, HVAC_ONTOLOGY, NETWORK_ONTOLOGY]


def resolve_canonical_class(user_text: str, *, domains=DEFAULT_DOMAINS) -> Optional[str]:
    """
    Ambiguity-safe, phrase-aware resolver:
    1) If multiple classes are explicitly mentioned anywhere → ``None``.
    2) Else, explicit detect per domain → return hit.
    3) Else, fuzzy guess per domain with moderate cutoff → return hit.
    """
    t = (user_text or "").lower()

    connectors = [" and ", " or ", ",", " to ", " with ", " & "]

    # 1) Global ambiguity check across domains
    explicit_terms: List[str] = []
    for onto in domains:
        for clazz, syns in onto.synonyms.items():
            terms = [clazz, *syns]
            if any(_phrase_present(t, term) for term in terms):
                explicit_terms.append(clazz)
    if len(set(explicit_terms)) >= 2 and any(c in t for c in connectors):
        return None

    # 2) Explicit detection per domain
    explicit_hits: List[str] = []
    for onto in domains:
        hit = onto.detect_explicit(t)
        if hit:
            explicit_hits.append(hit)
    if explicit_hits:
        return explicit_hits[0]

    # 3) Fuzzy guess
    for onto in domains:
        hit = onto.fuzzy_guess(t, cutoff=0.70)
        if hit:
            return hit

    return None


# Legacy compatibility - keep for existing SAAR integration
_CLASS_SYNONYMS: Dict[str, List[str]] = PV_ONTOLOGY.synonyms
_CLASS_ANCHORS: Dict[str, List[str]] = {
    "panel": ["Pmax", "W", "Voc", "Vmp", "Imp", "Isc", "area"],
    "inverter": ["AC rating", "kW", "MPPT", "AC output", "efficiency"],
    "battery": ["kWh", "DoD", "cycles", "BMS", "voltage"],
    "meter": ["class 1", "class 0.5", "accuracy", "ct ratio"],
    "controller": ["MPPT channels", "charge current"],
    "combiner": ["fuse", "strings", "touch safe"],
    "optimizer": ["module-level", "dc-dc", "efficiency"],
    "disconnect": ["switch", "isolation", "load break"],
}

@dataclass(frozen=True)
class OntologySpec:
    classes: Dict[str, List[str]]
    anchors: Dict[str, List[str]]

ONTOLOGY = OntologySpec(classes=_CLASS_SYNONYMS, anchors=_CLASS_ANCHORS)

def iter_prototype_texts() -> Dict[str, str]:
    """
    Build a small descriptive text per class; embeddings of these act as
    "prototypes" used for semantic similarity.
    """
    out: Dict[str, str] = {}
    for cls, syns in _CLASS_SYNONYMS.items():
        anchor = ", ".join(_CLASS_ANCHORS.get(cls, []))
        out[cls] = f"{cls}: synonyms({', '.join(syns)}); attributes({anchor})"
    return out
