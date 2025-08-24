from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


PROFILES_DIR = Path(__file__).parent / "data" / "profiles"


@dataclass
class TempRow:
    ambient_C_max: float
    factor: float


@dataclass
class GroupRow:
    cc_conductors_max: int
    factor: float


@dataclass
class StandardsProfile:
    id: str
    temp_rows: List[TempRow]
    group_rows: List[GroupRow]
    defaults_vdrop_pct: Dict[str, float]
    resistivity_ohm_per_km: Dict[str, float]
    mppt_window_margin_pct: float = 0.0


def load_profile(profile_id: str = "NEC_2023") -> StandardsProfile:
    p = PROFILES_DIR / f"{profile_id}.json"
    if not p.exists():
        raise FileNotFoundError(f"Standards profile not found: {p}")
    data = json.loads(p.read_text())
    return StandardsProfile(
        id=data["id"],
        temp_rows=[TempRow(**r) for r in data["ampacity_temperature_correction_90C"]],
        group_rows=[GroupRow(**r) for r in data["grouping_adjustment"]],
        defaults_vdrop_pct=data["defaults"]["voltage_drop_pct"],
        resistivity_ohm_per_km=data["resistivity_ohm_per_km"],
        mppt_window_margin_pct=float(data.get("mppt_window_margin_pct", 0.0)),
    )


def temp_correction_factor(ambient_C: float, prof: StandardsProfile) -> float:
    for r in prof.temp_rows:
        if ambient_C <= r.ambient_C_max:
            return r.factor
    return prof.temp_rows[-1].factor


def grouping_factor(n_ccc: int, prof: StandardsProfile) -> float:
    for r in prof.group_rows:
        if n_ccc <= r.cc_conductors_max:
            return r.factor
    return prof.group_rows[-1].factor


def default_vdrop_pct(circuit_kind: str, prof: StandardsProfile) -> float:
    return prof.defaults_vdrop_pct.get(circuit_kind, 3.0)


def resistivity(material: str, prof: StandardsProfile) -> float:
    return prof.resistivity_ohm_per_km.get(material, 0.018)


__all__ = [
    "StandardsProfile",
    "load_profile",
    "temp_correction_factor",
    "grouping_factor",
    "default_vdrop_pct",
    "resistivity",
]

