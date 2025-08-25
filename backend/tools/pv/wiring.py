from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text
from backend.tools.patch_builder import PatchBuilder
from math import ceil

async def generate_wiring(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """
    Generate intelligent electrical wiring using topology engine and create physical bundles & routes.
    """
    layer = args.get("layer", "single-line")
    ds = await store.get_meta(session_id)
    
    # Get current graph to analyze components
    from backend.database.session import get_session
    from backend.odl.store import ODLStore
    from backend.tools.electrical_topology import create_electrical_connections
    
    # Access database to get current graph
    async for db in get_session():
        odl_store = ODLStore()
        graph = await odl_store.get_graph(db, session_id)
        
        if not graph:
            return {}, {"title": "Error", "body": "Session not found"}, ["No session found"]
        
        # Convert ODL nodes to component format for topology engine
        components = {}
        for node_id, node in graph.nodes.items():
            components[node_id] = {
                "type": node.type,
                "attrs": node.attrs or {}
            }
        
        # Generate intelligent electrical connections
        electrical_connections = create_electrical_connections(components)
        
        # Build patch with electrical connections
        patch = PatchBuilder(f"{session_id}:generate_wiring")
        
        # 1) Create ODL edges for electrical connections
        connection_count = 0
        for conn in electrical_connections:
            edge_id = patch.add_edge(
                source_id=conn.source_component,
                target_id=conn.target_component, 
                kind="electrical",
                attrs={
                    "connection_type": conn.connection_type,
                    "source_terminal": conn.source_terminal,
                    "target_terminal": conn.target_terminal,
                    "layer": layer
                }
            )
            connection_count += 1
        
        break  # Exit the async generator loop
    
    # 2) Physical model: bundles and routes (enhanced based on actual connections)
    bundles = []
    routes = []
    
    strings = int(ds.get("design_state",{}).get("stringing",{}).get("strings",1))
    series = int(ds.get("design_state",{}).get("stringing",{}).get("series_per_string",8))
    mlpe = ds.get("design_state",{}).get("equip",{}).get("mlpe","none")
    
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
    
    # Store physical wiring model
    patch.set_meta(path="physical.bundles", data=bundles, merge=True)
    patch.set_meta(path="physical.routes", data=routes, merge=True)
    
    # Store electrical connection summary
    connection_summary = {
        "total_connections": connection_count,
        "dc_strings": len([c for c in electrical_connections if c.connection_type == "dc_string"]),
        "ac_circuits": len([c for c in electrical_connections if c.connection_type.startswith("ac_circuit")]),
        "generated_by": "electrical_topology_engine"
    }
    patch.set_meta(path="electrical.connections", data=connection_summary, merge=True)
    
    return patch.to_dict(), card_from_text(f"Generated {connection_count} electrical connections with intelligent topology engine."), []