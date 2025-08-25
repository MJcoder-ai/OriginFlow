from __future__ import annotations
"""
Copper THHN/THWN-2 ampacity & resistance with thermal/conduit derating helpers.
Ampacity at 60/75/90°C columns reflect NEC Table 310.16 magnitudes (illustrative, not verbatim).
"""
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Gauge:
    awg: str
    area_mm2: float
    ohm_per_km_75C: float
    ampacity_60C: int
    ampacity_75C: int
    ampacity_90C: int

AWG_DB: List[Gauge] = [
    Gauge("14", 2.08, 8.286, 20, 20, 25),
    Gauge("12", 3.31, 5.211, 25, 25, 30),
    Gauge("10", 5.26, 3.277, 30, 35, 40),
    Gauge("8", 8.37, 2.061, 40, 50, 55),
    Gauge("6", 13.3, 1.296, 55, 65, 75),
    Gauge("4", 21.2, 0.815, 70, 85, 95),
    Gauge("3", 26.7, 0.646, 85, 100, 110),
    Gauge("2", 33.6, 0.513, 95, 115, 130),
    Gauge("1", 42.4, 0.407, 110, 130, 145),
    Gauge("1/0", 53.5, 0.323, 125, 150, 170),
    Gauge("2/0", 67.4, 0.256, 145, 175, 195),
    Gauge("3/0", 85.0, 0.203, 165, 200, 225),
    Gauge("4/0", 107.2,0.161, 195, 230, 260),
]

def correction_factor_ambient(theta_C: float, insulation_class_C: int = 90) -> float:
    """
    Thermal correction factor ~ NEC Table 310.15(B)(1). Simplified curve for 90C insulation.
    """
    t = theta_C
    # piecewise approximation (engineers can swap with exact table)
    if t <= 30: return 1.00
    if t <= 35: return 0.96
    if t <= 40: return 0.91
    if t <= 45: return 0.87
    if t <= 50: return 0.82
    if t <= 55: return 0.76
    if t <= 60: return 0.71
    if t <= 70: return 0.58
    return 0.41

def adjustment_factor_current_carrying(ccc: int) -> float:
    """
    Conduit fill derate ~ NEC 310.15(C)(1) for 4-6, 7-9, 10-20 CCCs.
    """
    n = ccc
    if n <= 3: return 1.00
    if n <= 6: return 0.80
    if n <= 9: return 0.70
    if n <= 20: return 0.50
    if n <= 30: return 0.45
    return 0.40

def find_smallest_awg(required_ampacity: float, max_vdrop_pct: float, length_m_oneway: float,
                      current_A: float, system_V: float, temp_C: float, ccc: int) -> Dict:
    """
    Choose smallest gauge satisfying ampacity (after derating) and voltage-drop target.
    """
    k_amb = correction_factor_ambient(temp_C, 90)
    k_ccc = adjustment_factor_current_carrying(ccc)
    for g in AWG_DB:
        # Start from 90C column for THHN/THWN-2 in raceway
        Ider = g.ampacity_90C * k_amb * k_ccc
        if Ider < required_ampacity:  # ampacity check (incl. 125% cont. assumed in required_ampacity)
            continue
        # Voltage drop calc
        R = g.ohm_per_km_75C / 1000.0  # Ω/m (use 75C column to be conservative)
        vd_pct = 2 * current_A * length_m_oneway * R / system_V * 100.0
        if vd_pct <= max_vdrop_pct:
            return {"awg": g.awg, "ampacity_derated_A": round(Ider,1), "vd_pct": round(vd_pct,2)}
    # If nothing fits, return largest
    last = AWG_DB[-1]
    R = last.ohm_per_km_75C/1000.0
    vd_pct = 2*current_A*length_m_oneway*R/system_V*100.0
    return {"awg": last.awg, "ampacity_derated_A": last.ampacity_90C*k_amb*k_ccc, "vd_pct": round(vd_pct,2)}