"""
Task router: translate high-level tasks into typed tool invocations.

The router never touches the database or ODL store; it builds tool inputs
from minimal context and returns the resulting ODLPatch (or None).
"""
from __future__ import annotations

from typing import Optional, Dict, List
from pydantic import BaseModel, Field

from backend.odl.schemas import ODLPatch, ODLNode
from backend.tools.schemas import (
    GenerateWiringInput,
    GenerateMountsInput,
    AddMonitoringInput,
    MakePlaceholdersInput,
    DeleteNodesInput,
    AddProtectiveDeviceInput,
)
from backend.tools import wiring, structural, monitoring, placeholders, deletion
from backend.tools import protective_devices, electrical
from backend.tools import electrical_v2  # new v2 tools
from backend.tools import design_state, standards_check_v2
from backend.tools import schedules as schedules_tool
from backend.tools import explain_design_v2
from backend.tools import routing, mechanical
from backend.tools import labels as labels_tool
from backend.tools import select_equipment, stringing, ocp_dc, materialize, bom as bom_tool
from backend.tools.pv import (
    assumptions, select_components, stringing as pv_stringing, 
    apply_stringing, disconnects, protection, conductors, 
    wiring as pv_wiring, compliance, bom as pv_bom, explain
)
from backend.tools.mech import surface, racking
from backend.orchestrator.plan_spec import PlanSpec
from backend.orchestrator.auto_designer import run_auto_design, auto_design_from_nl
from backend.tools.standards_profiles import load_profile
from backend.ai.tools.generate_wiring_advanced import generate_wiring_advanced
from backend.odl.schemas import ODLGraph, ODLEdge, PatchOp
import asyncio
import logging
from backend.tools.replacement import apply_replacements, ReplaceInput, ReplacementItem

TOOL_COUNTERS: Dict[str, int] = {}

# Phase gating: what categories are allowed in each workflow phase
PHASE_ALLOW = {
    "setup": {"compute_design_state", "select_equipment", "select_dc_stringing", "check_compliance_v2", "explain_design_v2"},
    "proposal": {"select_equipment", "select_dc_stringing", "check_compliance_v2", "select_ocp_dc", "select_ocp_ac_v2", "select_conductors_v2"},
    "materialize": "ANY",
}


def enforce_phase(phase: str, task_id: str) -> bool:
    allow = PHASE_ALLOW.get(phase, "ANY")
    if allow == "ANY":
        return True
    return task_id in allow


def get_tool(task_id: str):
    mapping = {
        # existing tools
        "select_ocp_ac": electrical.select_ocp_ac,
        "select_conductors": electrical.select_conductors,
        "expand_connections": electrical.expand_connections,
        # v2 tools
        "select_ocp_ac_v2": electrical_v2.select_ocp_ac_v2,
        "select_conductors_v2": electrical_v2.select_conductors_v2,
        "expand_connections_v2": electrical_v2.expand_connections_v2,
        # state & compliance
        "compute_design_state": design_state.compute_design_state,
        "check_compliance_v2": standards_check_v2.check_compliance_v2,
        "generate_schedules": schedules_tool.generate_schedules,
        "explain_design_v2": explain_design_v2.explain_design_v2,
        # new tools
        "plan_routes": routing.plan_routes,
        "layout_racking": mechanical.layout_racking,
        "attachment_spacing": mechanical.attachment_spacing,
        "generate_labels": labels_tool.generate_labels,
        "select_equipment": select_equipment.select_equipment,
        "select_dc_stringing": stringing.select_dc_stringing,
        "select_ocp_dc": ocp_dc.select_ocp_dc,
        "materialize_design": materialize.materialize_design,
        "generate_bom": bom_tool.generate_bom,
        "auto_design": run_auto_design,  # takes PlanSpec
        # chat convenience: NL -> PlanSpec -> auto design (simulate-first)
        "auto_design_from_nl": auto_design_from_nl,
        # protective devices
        "add_protective_device": protective_devices.add_protective_device,
        # PV tools
        "pv_set_assumptions": assumptions.set_assumptions,
        "pv_select_components": select_components.run,
        "pv_stringing_plan": pv_stringing.plan,
        "pv_apply_stringing": apply_stringing.apply_stringing,
        "pv_add_disconnects": disconnects.add_disconnects,
        "pv_size_protection": protection.size_protection,
        "pv_size_conductors": conductors.size_conductors,
        "pv_generate_wiring": pv_wiring.generate_wiring,
        "pv_compliance_check": compliance.compliance_check,
        "pv_compute_bom": pv_bom.compute_bom,
        "pv_explain": explain.run,
        # Mechanical tools
        "mech_surface": surface.run,
        "mech_racking_layout": racking.layout,
        "mech_attachment_check": racking.attachments_check,
    }
    return mapping.get(task_id)


def get_standards_profile(profile_id: str = "NEC_2023"):
    return load_profile(profile_id).id


async def _bridge_advanced_wiring(inp: GenerateWiringInput) -> Optional[ODLPatch]:
    """Bridge function to call async advanced wiring and return ODLPatch"""
    try:
        # Create ODLGraph from the input
        nodes = {node.id: node for node in inp.view_nodes}
        graph = ODLGraph(
            session_id=inp.session_id,
            version=1,  # Version doesn't matter for this operation
            nodes=nodes,
            edges=[]
        )
        
        # Call the advanced wiring system
        async def _run_advanced_wiring():
            return await generate_wiring_advanced(
                graph=graph,
                session_id=inp.session_id,
                layer="single-line",
                system_type="string_inverter",
                protection_level="standard"
            )
        
        # Run the async function inside the current event loop
        result = await _run_advanced_wiring()
        
        if not result.get("success"):
            # Fall back to simple wiring if advanced fails
            return wiring.generate_wiring(inp)
        
        # Convert the edges from the graph to patch operations
        ops = []
        for i, edge in enumerate(graph.edges):
            op_id = f"{inp.request_id}:advanced_edge:{i+1}"
            ops.append(PatchOp(
                op_id=op_id,
                op="add_edge",
                value={
                    "id": edge.id,
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "kind": edge.kind,
                    "attrs": edge.attrs or {}
                }
            ))
        
        # Also add any protection device nodes that were created
        wiring_applied = result.get("wiring_applied", {})
        if wiring_applied.get("nodes_added", 0) > 0:
            for node_id, node in graph.nodes.items():
                # Check if this is a newly added node (not in original view)
                if not any(n.id == node_id for n in inp.view_nodes):
                    op_id = f"{inp.request_id}:advanced_node:{node_id}"
                    ops.append(PatchOp(
                        op_id=op_id,
                        op="add_node",
                        value={
                            "id": node.id,
                            "type": node.type,
                            "component_master_id": node.component_master_id,
                            "attrs": node.attrs or {}
                        }
                    ))
        
        from backend.tools.schemas import make_patch
        return make_patch(inp.request_id, ops=ops)
        
    except Exception as e:
        # Fall back to simple wiring on any error
        logger = logging.getLogger(__name__)
        logger.warning(f"Advanced wiring failed, falling back to simple wiring: {e}")
        return wiring.generate_wiring(inp)


class ActArgs(BaseModel):
    layer: str = Field("single-line", description="ODL layer for the tool view")
    # Tool-specific args (optional)
    edge_kind: str | None = None
    mount_type: str | None = None
    device_type: str | None = None
    placeholder_type: str | None = None
    component_type: str | None = None
    component_types: list[str] | None = None
    count: int | None = None
    attrs: dict[str, object] | None = None
    # Replacement-specific extras
    requirements: dict[str, float] | None = None
    categories: list[str] | None = None
    # Optional explicit candidate pool (bypass DB)
    pool: list[dict] | None = None
    # Protective device-specific
    connection_mode: str | None = None
    existing_components: list[str] | None = None
    rating_A: float | None = None
    voltage_rating_V: float | None = None


async def run_task(
    *,
    task: str,
    session_id: str,
    request_id: str,
    layer_nodes: list[ODLNode],
    args: ActArgs,
    db: Optional[object] = None,
) -> Optional[ODLPatch]:
    """Build tool input for `task`, invoke, and return an ODLPatch (or None)."""
    if task == "generate_wiring":
        inp = GenerateWiringInput(
            session_id=session_id,
            request_id=request_id,
            view_nodes=layer_nodes,
            edge_kind=args.edge_kind or "electrical",
        )
        # prefer advanced wiring; fall back handled inside the bridge
        return await _bridge_advanced_wiring(inp)

    if task == "generate_mounts":
        inp = GenerateMountsInput(
            session_id=session_id,
            request_id=request_id,
            view_nodes=layer_nodes,
            mount_type=args.mount_type or "mount",
            layer=args.layer or "structural",
        )
        return structural.generate_mounts(inp)

    if task == "add_monitoring":
        inp = AddMonitoringInput(
            session_id=session_id,
            request_id=request_id,
            view_nodes=layer_nodes,
            device_type=args.device_type or "monitoring",
            layer=args.layer or "electrical",
        )
        return monitoring.add_monitoring_device(inp)

    if task == "make_placeholders":
        placeholder_type = (
            args.placeholder_type
            or args.component_type
            or "generic_panel"
        )
        inp = MakePlaceholdersInput(
            session_id=session_id,
            request_id=request_id,
            count=args.count or 1,
            placeholder_type=placeholder_type,
            attrs=args.attrs or {"layer": args.layer},
        )
        return placeholders.make_placeholders(inp)

    if task == "delete_nodes":
        ctypes = args.component_types or []
        inp = DeleteNodesInput(
            session_id=session_id,
            request_id=request_id,
            view_nodes=layer_nodes,
            component_types=ctypes,
        )
        return deletion.delete_nodes(inp)

    if task == "add_protective_device":
        inp = AddProtectiveDeviceInput(
            session_id=session_id,
            request_id=request_id,
            view_nodes=layer_nodes,
            device_type=args.device_type or "dc_switch",
            layer=args.layer or "single-line",
            connection_mode=args.connection_mode or "series_insertion",
            existing_components=args.existing_components or [],
            rating_A=args.rating_A,
            voltage_rating_V=args.voltage_rating_V,
        )
        return protective_devices.add_protective_device(inp)

    # Replacement patch is constructed by orchestrator (after choosing candidates)
    if task == "replace_placeholders":
        # The orchestrator composes replacements; run_task simply wraps into a patch.
        # We expect args.attrs['repl_items'] as a list of {node_id, part_number, new_type?, attrs?}
        items = (args.attrs or {}).get("repl_items") or []
        repls = [ReplacementItem(**it) for it in items]
        inp = ReplaceInput(session_id=session_id, request_id=request_id, replacements=repls)
        return apply_replacements(inp)

    # Handle PV tools - these use a different calling convention
    tool_func = get_tool(task)
    if tool_func:
        # PV tools expect different arguments - adapt them here
        if task.startswith("pv_"):
            from backend.odl.store import ODLStore
            
            # PV tools expect: store, session_id, args dict  
            store = ODLStore()
            # Add compatibility methods for PV tools that expect different APIs
            if not hasattr(store, 'get_odl'):
                # Create a wrapper that provides the database session
                async def get_odl_wrapper(session_id_param):
                    if db:
                        return await store.get_graph(db, session_id_param)
                    else:
                        # Fallback - try to get a temporary db session
                        from backend.database.session import get_session
                        async for temp_db in get_session():
                            return await store.get_graph(temp_db, session_id_param)
                store.get_odl = get_odl_wrapper
                
            # Add get_meta compatibility wrapper
            if not hasattr(store, 'get_meta'):
                async def get_meta_wrapper(session_id_param):
                    if db:
                        graph = await store.get_graph(db, session_id_param)
                        return graph.meta if graph else {}
                    else:
                        from backend.database.session import get_session
                        async for temp_db in get_session():
                            graph = await store.get_graph(temp_db, session_id_param)
                            return graph.meta if graph else {}
                store.get_meta = get_meta_wrapper
            pv_args = {
                "layer": args.layer,
                **(args.attrs or {})
            }
            
            # Add command if provided (for tools that parse NL requirements)
            if hasattr(args, 'command') and args.command:
                pv_args["command"] = args.command
            
            try:
                # Call the PV tool function with expected signature: store, session_id, args
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(store=store, session_id=session_id, args=pv_args)
                else:
                    result = tool_func(store=store, session_id=session_id, args=pv_args)
                
                # PV tools return (patch_dict, card_dict, warnings) tuple
                if isinstance(result, tuple) and len(result) >= 1:
                    patch_dict = result[0]
                    if isinstance(patch_dict, dict) and "operations" in patch_dict:
                        from backend.tools.schemas import make_patch
                        return make_patch(request_id, ops=patch_dict["operations"])
                    elif patch_dict:
                        # Convert patch dict to ODLPatch
                        from backend.odl.schemas import ODLPatch
                        return ODLPatch.model_validate(patch_dict)
                
                # Fallback - create empty patch
                from backend.tools.schemas import make_patch
                return make_patch(request_id, ops=[])
                    
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"PV tool {task} failed: {e}")
                import traceback
                logger.warning(f"PV tool traceback: {traceback.format_exc()}")
                return None
    
    return None
