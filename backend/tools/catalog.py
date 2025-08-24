from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any


CAT_DIR = Path(__file__).parent / "data" / "catalog"


@dataclass
class ModuleItem:
    id: str
    title: str
    p_W: float
    voc: float
    vmp: float
    isc: float
    imp: float
    beta_voc_pct_per_C: float


@dataclass
class InverterItem:
    id: str
    title: str
    ac_kW: float
    ac_V: str
    phases: str
    max_system_vdc: float
    mppt_windows: List[Dict[str, float]]


def _load(path: Path) -> List[Dict[str, Any]]:
    return json.loads(path.read_text())


def load_modules() -> List[ModuleItem]:
    return [ModuleItem(**x) for x in _load(CAT_DIR / "modules.json")]


def load_inverters() -> List[InverterItem]:
    return [InverterItem(**x) for x in _load(CAT_DIR / "inverters.json")]


__all__ = ["ModuleItem", "InverterItem", "load_modules", "load_inverters"]

