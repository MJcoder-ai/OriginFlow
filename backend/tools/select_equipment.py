from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, make_patch
from backend.tools.catalog import load_modules, load_inverters, ModuleItem, InverterItem


class SelectEquipmentInput(ToolBase):
    target_kw_stc: float
    preferred_module_W: float | None = None
    inverter_kw_window: tuple[float, float] = (0.7, 1.2)  # inverter AC size relative to DC target


def _choose_module(target_kw: float, preferred_W: float | None, modules: List[ModuleItem]) -> ModuleItem:
    if preferred_W:
        byW = sorted(modules, key=lambda m: abs(m.p_W - preferred_W))
        return byW[0]
    # Pick mid-bin module
    return sorted(modules, key=lambda m: abs(m.p_W - 400))[0]


def _choose_inverter(target_kw: float, window: tuple[float, float], inverters: List[InverterItem]) -> InverterItem:
    lo = target_kw * window[0]
    hi = target_kw * window[1]
    # Prefer the smallest inverter within window; fallback to nearest above
    cands = [i for i in inverters if lo <= i.ac_kW <= hi]
    if not cands:
        above = [i for i in inverters if i.ac_kW >= lo]
        return sorted(above, key=lambda i: i.ac_kW)[0] if above else sorted(inverters, key=lambda i: i.ac_kW)[-1]
    return sorted(cands, key=lambda i: i.ac_kW)[0]


def select_equipment(inp: SelectEquipmentInput):
    mods = load_modules()
    invs = load_inverters()
    m = _choose_module(inp.target_kw_stc, inp.preferred_module_W, mods)
    inv = _choose_inverter(inp.target_kw_stc, inp.inverter_kw_window, invs)
    equip = {
        "module": m.__dict__,
        "inverter": {
            **inv.__dict__,
            "mppt_count": sum(w.get("count", 1) for w in inv.mppt_windows),
        },
    }
    ops: List[PatchOp] = []
    # Persist to meta.design_state.equip (state only)
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:meta:equip",
            op="set_meta",
            value={"path": "design_state.equip", "merge": True, "data": equip},
        )
    )
    # Annotation
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:equip",
            op="add_edge",
            value={
                "id": f"ann:equip:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "select_equipment",
                    "summary": f"{m.title} + {inv.title}",
                },
            },
        )
    )
    return make_patch(inp.request_id, ops)


__all__ = ["SelectEquipmentInput", "select_equipment"]

