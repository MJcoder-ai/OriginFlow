from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

_KW = re.compile(r"(?P<val>\d+(?:\.\d+)?)\s*(?:kW|KW|kw)\b")
_W = re.compile(r"(?P<val>\d+(?:\.\d+)?)\s*(?:W|w)\b")
_QTY = re.compile(r"\b(?P<val>\d{1,4})\s*(?:x|units?|pcs?|panels?|modules?|inverters?)\b", re.I)


@dataclass
class PVIntent:
    system_kw: Optional[float] = None
    module_watts: Optional[float] = None
    inverter_qty: Optional[int] = None
    panel_qty: Optional[int] = None


def parse_pv_intent(text: str) -> PVIntent:
    t = text or ""
    intent = PVIntent()
    if m := _KW.search(t):
        intent.system_kw = float(m.group("val"))
    watts = [float(m.group("val")) for m in _W.finditer(t)]
    if watts:
        plausible = [w for w in watts if 150 <= w <= 900]
        if plausible:
            intent.module_watts = min(plausible)
    for m in _QTY.finditer(t):
        qty = int(m.group("val"))
        noun_span = t[m.end(): m.end()+16].lower()
        if "inverter" in noun_span:
            intent.inverter_qty = qty
        elif "panel" in noun_span or "module" in noun_span:
            intent.panel_qty = qty
    return intent


def clamp_count(val: int, *, lo: int = 1, hi: int = 256) -> int:
    return max(lo, min(hi, int(val)))
