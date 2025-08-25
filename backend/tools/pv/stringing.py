from __future__ import annotations
from typing import Any, Dict, Tuple, List
from backend.odl.schemas import ODLPatch
from math import ceil
from backend.utils.adpf import card_from_text

def _worst_case_voc(voc_stc: float, t_min_c: float = -10.0) -> float:
    """Worst-case Voc at minimum temperature."""
    return voc_stc * (1 + (t_min_c - 25) * (-0.0028))

def query_nodes(graph, layer: str, kind: str) -> List:
    """Simple placeholder to query nodes from ODL graph."""
    # Placeholder implementation - would use actual ODL querying
    if kind == "panel":
        return [type('Node', (), {'attrs': {'voc': 49.5, 'vmp': 41.5}})() for _ in range(8)]
    elif kind == "inverter":
        return [type('Node', (), {'attrs': {'vdc_max': 600, 'mppts': 2, 'mppt_vmin': 200, 'mppt_vmax': 550}})()]
    return []

async def plan(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Plan stringing with MPPT window checks and MLPE support."""
    layer = args.get("layer", "single-line")
    graph = await store.get_odl(session_id)
    panels = query_nodes(graph, layer=layer, kind="panel")
    inverters = query_nodes(graph, layer=layer, kind="inverter")
    if not panels or not inverters:
        return {}, card_from_text("No panels/inverter found for stringing."), []
    
    inv = inverters[0]
    voc = float(panels[0].attrs.get("voc", 49.5))
    vdc_max = float(inv.attrs.get("vdc_max", 600))
    vmp = float(panels[0].attrs.get("vmp", 41.5))
    mppts = int(inv.attrs.get("mppts", 2))
    mppt_vmin = float(inv.attrs.get("mppt_vmin", 200))
    mppt_vmax = float(inv.attrs.get("mppt_vmax", 550))
    # env (for Tmin)
    ds = await store.get_meta(session_id)
    tmin = float(ds.get("design_state", {}).get("env", {}).get("tmin_C", -10.0))
    mlpe_mode = ds.get("design_state",{}).get("equip",{}).get("mlpe","none")
    s_voc = _worst_case_voc(voc, t_min_c=tmin)
    total = len(panels)
    if mlpe_mode == "microinverter":
        series = 1; strings = total
        rationale = "Microinverters: one module per inverter, AC trunk wiring."
    else:
        # Series N must satisfy Voc_cold*N < 0.98*Vdc_max and mppt_vmin <= Vmp*N <= mppt_vmax
        n_ok = []
        for N in range(2, 25):
            vocN = s_voc * N
            vmpN = vmp * N
            if vocN <= 0.98*vdc_max and mppt_vmin <= vmpN <= mppt_vmax:
                n_ok.append(N)
        if not n_ok:
            n_ok = [max(2, int(0.98*vdc_max/s_voc))]
        series = max(n_ok)
        strings = ceil(total / series)
        strings = max(strings, mppts)  # at least one per MPPT
        rationale = f"String inverter: MPPT window {mppt_vmin}-{mppt_vmax} V; choose {series} in series."
    # save proposal to meta
    meta_patch = ODLPatch()
    meta_patch.set_meta(path="design_state.stringing", data={
        "series_per_string": series,
        "strings": strings,
        "modules_total": total,
        "voc_cold_V": round(s_voc, 2),
        "vmp_string_V": round(vmp * series, 2)
    }, merge=True)
    plan = {
        "series_per_string": series,
        "strings": strings,
        "mppt": mppts,
    }
    card = {
        "title": "Stringing Plan",
        "body": f"{total} panels → {strings} strings × {series} series. {rationale} (Voc@Tmin≈{s_voc:.1f} V, vdc_max={vdc_max} V).",
        "data": plan,
    }
    return meta_patch.to_dict(), card, []