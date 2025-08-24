from __future__ import annotations
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class RoofPlane(BaseModel):
    id: str
    tilt_deg: float
    azimuth_deg: float
    w: float
    h: float
    setbacks_m: float = 0.5


class Env(BaseModel):
    site_tmin_C: float = -10.0
    site_tmax_C: float = 45.0
    utility: str = "120/240V"
    profile: str = "NEC_2023"


class Targets(BaseModel):
    dc_kw_stc: float
    vd_dc_pct: float = 2.0
    vd_ac_pct: float = 3.0


class Constraints(BaseModel):
    bus_A: int = 200
    main_A: int = 200
    interconnection: str = "load_side"


class Preferences(BaseModel):
    optimizer: str = "cost"
    mlpe: str = "auto"  # "required" | "none" | "auto"


class PlanSpec(BaseModel):
    scope: str = "pv_resi_grid_tied"
    env: Env
    targets: Targets
    constraints: Constraints = Constraints()
    preferences: Preferences = Preferences()
    inputs_optional: Dict = Field(default_factory=dict)  # roof, waypoints, etc.


__all__ = ["PlanSpec", "Env", "Targets", "Constraints", "Preferences", "RoofPlane"]

