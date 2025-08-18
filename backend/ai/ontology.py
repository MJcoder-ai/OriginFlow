from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

# NOTE:
#  - These are *class prototypes* (not individual SKUs) the resolver uses to
#    compute similarity between user text and domain classes.
#  - The embedder is provided by the embedding service at runtime.

_CLASS_SYNONYMS: Dict[str, List[str]] = {
    "panel": [
        "pv module", "solar module", "solar panel", "pv panel", "module", "array",
        "panel string", "panel unit"
    ],
    "inverter": [
        "inverter", "string inverter", "microinverter", "micro inverter",
        "ac inverter", "dc-ac converter"
    ],
    "battery": ["battery", "bess", "energy storage", "storage module"],
    "meter": ["meter", "kwh meter", "revenue meter", "ct", "current transformer"],
    "controller": ["mppt", "charge controller", "controller"],
    "combiner": ["combiner", "combiner box", "string combiner"],
    "optimizer": ["optimizer", "dc optimizer"],
    "disconnect": ["disconnect", "isolator", "ac disconnect", "dc disconnect"],
}

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
