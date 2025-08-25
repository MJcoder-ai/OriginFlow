from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text
from backend.tools.patch_builder import PatchBuilder
from math import ceil

async def generate_wiring(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """
    Generate SLD wiring and persist physical bundles & routes with approximate lengths.
    """
    layer = args.get("layer", "single-line")
    ds = await store.get_meta(session_id)
    strings = int(ds.get("design_state",{}).get("stringing",{}).get("strings",1))
    series = int(ds.get("design_state",{}).get("stringing",{}).get("series_per_string",8))
    mlpe = ds.get("design_state",{}).get("equip",{}).get("mlpe","none")
    patch = PatchBuilder(f"{session_id}:generate_wiring")
    # 1) Link graph (existing auto-link)
    patch.auto_link(layer=layer)
    # 2) Physical model: bundles and routes (very simple estimates; later swap with router)
    bundles = []
    routes = []
    if mlpe == "microinverter":
        trunk_len_m = 18.0
        bundles.append({"name":"AC_TRUNK","conductors":[{"role":"L1"},{"role":"L2"},{"role":"N"},{"role":"PE"}], "length_m": trunk_len_m})
        routes.append({"bundle":"AC_TRUNK","segments":[{"from":"roof","to":"inverter","len_m":trunk_len_m}]})
    else:
        # DC strings from array to inverter combiner
        for s in range(1, strings+1):
            Lm = 12.0 + 0.8*series  # crude: longer with more modules
            bname = f"STR_{s}"
            bundles.append({"name": bname, "conductors":[{"role":"PV+"},{"role":"PV-"},{"role":"EGC"}], "length_m": Lm})
            routes.append({"bundle": bname, "segments":[{"from":f"array_s{s}","to":"inverter","len_m":Lm}]})
    patch.set_meta(path="physical.bundles", data=bundles, merge=False)
    patch.set_meta(path="physical.routes", data=routes, merge=False)
    return patch.to_dict(), card_from_text("Generated wiring with bundles/routes and approximate lengths."), []