from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.tools.patch_builder import PatchBuilder
from backend.utils.adpf import card_from_text

async def run(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """
    Create/ensure inverter (or MLPE) and panel placeholders.
    """
    count = int(args.get("panel_count", 8))
    layer = args.get("layer", "single-line")
    mlpe = args.get("mlpe", "none")  # none | optimizer | microinverter
    # Build a simple ODLPatch that adds one inverter node and N panel nodes (placeholder attributes kept)
    patch = PatchBuilder(f"{session_id}:select_components")
    inv_attrs = {"mppts": 2, "vdc_max": 600, "mppt_vmin":200, "mppt_vmax":550, **args.get("inverter_hint", {})}
    patch.add_node(kind="inverter", attrs=inv_attrs, layer=layer)
    for _ in range(count):
        patch.add_node(kind="panel", attrs=args.get("module_hint", {}), layer=layer)
    # Persist selection to meta for later tools
    equip_meta = {
        "inverter": {"ac_kw": args.get("inverter_hint",{}).get("ac_kw",3.8),
                     "vdc_max": inv_attrs["vdc_max"], "mppt_vmin": inv_attrs["mppt_vmin"], "mppt_vmax": inv_attrs["mppt_vmax"],
                     "mppts": inv_attrs["mppts"], "topology": "string"},
        "module": args.get("module_hint", {}),
        "mlpe": mlpe
    }
    patch.set_meta(path="design_state.equip", data=equip_meta, merge=True)
    if mlpe == "microinverter":
        for _ in range(count):
            patch.add_node(kind="microinverter", attrs={"ac_trunk": True}, layer=layer)
    if mlpe == "optimizer":
        # Not adding nodes per-module in SLD; record mode for routing
        pass
    return patch.to_dict(), card_from_text(f"Added inverter + {count} panels (placeholders){' with MLPE: '+mlpe if mlpe!='none' else ''}."), []