from __future__ import annotations
from typing import List, Dict, Any
from backend.tools.schemas import make_patch
from backend.odl.schemas import PatchOp, ODLPatch
from backend.orchestrator.plan_spec import PlanSpec
from backend.tools import design_state, standards_check_v2, electrical_v2
from backend.tools import select_equipment, stringing, ocp_dc, materialize, schedules as schedules_tool
from backend.tools import routing, mechanical, labels as labels_tool, bom as bom_tool, explain_design_v2
from backend.tools.nl.parse_plan_spec import parse_plan_spec, NLToPlanSpecInput


def _collect_ops(*patches: ODLPatch | Dict[str, Any]) -> List[PatchOp]:
    ops: List[PatchOp] = []
    for p in patches:
        if not p:
            continue
        if isinstance(p, dict):
            ops.extend(p.get("ops", []))
        else:
            ops.extend(getattr(p, "operations", []))
    return ops


def run_auto_design(spec: PlanSpec, session_id: str, request_id: str, simulate: bool = True) -> ODLPatch:
    """End-to-end planner. Returns an ODLPatch (not applied) that the UI can preview."""
    ops: List[PatchOp] = []
    # 1) design state
    ds_patch = design_state.compute_design_state(
        design_state.ComputeDesignStateInput(
            session_id=session_id,
            request_id=f"{request_id}:ds",
            env=design_state.Env(
                site_tmin_C=spec.env.site_tmin_C,
                site_tmax_C=spec.env.site_tmax_C,
                code_profile=spec.env.profile,
            ),
            modules=[],
            inverters=[],
            view_nodes=[],
        )
    )
    ops += _collect_ops(ds_patch)

    # 2) equipment
    eq_patch = select_equipment.select_equipment(
        select_equipment.SelectEquipmentInput(
            session_id=session_id,
            request_id=f"{request_id}:equip",
            target_kw_stc=spec.targets.dc_kw_stc,
        )
    )
    ops += _collect_ops(eq_patch)

    # 3) stringing (use catalog first item for simplicity)
    from backend.tools.catalog import load_modules, load_inverters

    m = load_modules()[0]
    inv = load_inverters()[0]
    str_patch = stringing.select_dc_stringing(
        stringing.SelectStringingInput(
            session_id=session_id,
            request_id=f"{request_id}:string",
            target_kw_stc=spec.targets.dc_kw_stc,
            env=stringing.Env(site_tmin_C=spec.env.site_tmin_C),
            module=stringing.Module(
                p_W=m.p_W,
                voc=m.voc,
                vmp=m.vmp,
                imp=m.imp,
                beta_voc_pct_per_C=m.beta_voc_pct_per_C,
            ),
            inverter=stringing.Inverter(
                max_system_vdc=inv.max_system_vdc,
                mppt_windows=[stringing.MpptWindow(**w) for w in inv.mppt_windows],
            ),
        )
    )
    ops += _collect_ops(str_patch)

    # 4) fast compliance check (gate)
    from backend.tools.standards_check_v2 import (
        CheckComplianceV2Input,
        Env as CEnv,
        Module as CMod,
        Inverter as CInv,
        MPPT,
    )

    comp = standards_check_v2.check_compliance_v2(
        CheckComplianceV2Input(
            session_id=session_id,
            request_id=f"{request_id}:cc0",
            env=CEnv(
                site_tmin_C=spec.env.site_tmin_C,
                site_tmax_C=spec.env.site_tmax_C,
                code_profile=spec.env.profile,
            ),
            module=CMod(
                voc_stc=m.voc,
                vmp=m.vmp,
                isc_stc=m.isc,
                beta_voc_pct_per_C=m.beta_voc_pct_per_C,
            ),
            inverter=CInv(
                max_system_vdc=inv.max_system_vdc,
                mppt=MPPT(
                    v_min=inv.mppt_windows[0]["v_min"],
                    v_max=inv.mppt_windows[0]["v_max"],
                    count=inv.mppt_windows[0].get("count", 1),
                ),
            ),
            dc_series_count=7,
        )
    )
    ops += _collect_ops(comp)

    # 5) DC OCPD determination
    ocpdc = ocp_dc.select_ocp_dc(
        ocp_dc.SelectOcpDcInput(
            session_id=session_id,
            request_id=f"{request_id}:ocpdc",
            strings_parallel=2,
            module=ocp_dc.Module(isc=m.isc),
        )
    )
    ops += _collect_ops(ocpdc)

    # 6) AC OCPD
    acpd = electrical_v2.select_ocp_ac_v2(
        electrical_v2.SelectOcpACV2Input(
            session_id=session_id,
            request_id=f"{request_id}:ocpac",
            inverter_inom_A=round((inv.ac_kW * 1000) / 240.0, 2),
        )
    )
    ops += _collect_ops(acpd)

    # 7) Conductors (first pass – nominal lengths)
    cdc = electrical_v2.select_conductors_v2(
        electrical_v2.SelectConductorsV2Input(
            session_id=session_id,
            request_id=f"{request_id}:cdc",
            circuit_kind="dc_string",
            current_A=10.7,
            length_m=15.0,
            system_v=290.0,
        )
    )
    cac = electrical_v2.select_conductors_v2(
        electrical_v2.SelectConductorsV2Input(
            session_id=session_id,
            request_id=f"{request_id}:cac",
            circuit_kind="ac_feeder",
            current_A=round((inv.ac_kW * 1000) / 240.0, 2),
            length_m=20.0,
            system_v=240.0,
        )
    )
    ops += _collect_ops(cdc, cac)

    # 8) Materialize nodes/edges (simulate switch)
    mats = materialize.materialize_design(
        materialize.MaterializeDesignInput(
            session_id=session_id,
            request_id=f"{request_id}:mat",
            simulate=simulate,
            inverter_id=inv.id,
            inverter_title=inv.title,
            mppts=sum(w.get("count", 1) for w in inv.mppt_windows),
            modules=14 if spec.targets.dc_kw_stc >= 5 else 8,
            modules_per_string=7 if spec.targets.dc_kw_stc >= 5 else 8,
            strings_parallel=2 if spec.targets.dc_kw_stc >= 5 else 1,
        )
    )
    ops += _collect_ops(mats)

    # 9) Expand connections (bundle edges)
    exp = electrical_v2.expand_connections_v2(
        electrical_v2.ExpandConnectionsV2Input(
            session_id=session_id,
            request_id=f"{request_id}:expand",
            source_id="INV1",
            target_id="MAIN" if not simulate else "MAIN",
            connection_type="ac_1ph_3w",
            add_ground=True,
        )
    )
    ops += _collect_ops(exp)

    # 10) Route bundles (compute lengths)
    routes = routing.plan_routes(
        routing.PlanRoutesInput(
            session_id=session_id,
            request_id=f"{request_id}:route",
            bundles=[
                routing.BundleRef(
                    id="bundle:INV1:MAIN:ac_1ph_3w",
                    source_id="INV1",
                    target_id="MAIN",
                    system="ac_1ph_3w",
                    attrs={},
                )
            ],
            node_poses={"INV1": routing.Pose(x=0, y=0), "MAIN": routing.Pose(x=10, y=0)},
            default_length_m=10.0,
        )
    )
    ops += _collect_ops(routes)

    # 11) Mechanical
    mech = mechanical.layout_racking(
        mechanical.LayoutRackingInput(
            session_id=session_id,
            request_id=f"{request_id}:mech",
            roof=mechanical.RoofPlane(
                id="R1",
                tilt_deg=25,
                azimuth_deg=180,
                width_m=11.0,
                height_m=6.0,
                setback_m=0.5,
            ),
            modules_count=14 if spec.targets.dc_kw_stc >= 5 else 8,
        )
    )
    ops += _collect_ops(mech)

    # 12) Schedules (uses routes)
    route_data = []
    for op in routes.operations:
        if op.op == "set_meta" and op.value.get("path") == "physical.routes":
            route_data = op.value.get("data", [])
            break
    sch = schedules_tool.generate_schedules(
        schedules_tool.GenerateSchedulesInput(
            session_id=session_id,
            request_id=f"{request_id}:sched",
            view_edges=[],
            routes=route_data,
        )
    )
    ops += _collect_ops(sch)

    # 13) Labels
    labs = labels_tool.generate_labels(
        labels_tool.GenerateLabelsInput(
            session_id=session_id,
            request_id=f"{request_id}:labels",
            view_nodes=[],
            view_edges=[],
        )
    )
    ops += _collect_ops(labs)

    # 14) Final compliance (lightweight)
    final = standards_check_v2.check_compliance_v2(
        CheckComplianceV2Input(
            session_id=session_id,
            request_id=f"{request_id}:ccf",
            env=CEnv(
                site_tmin_C=spec.env.site_tmin_C,
                site_tmax_C=spec.env.site_tmax_C,
                code_profile=spec.env.profile,
            ),
            module=CMod(
                voc_stc=m.voc,
                vmp=m.vmp,
                isc_stc=m.isc,
                beta_voc_pct_per_C=m.beta_voc_pct_per_C,
            ),
            inverter=CInv(
                max_system_vdc=inv.max_system_vdc,
                mppt=MPPT(
                    v_min=inv.mppt_windows[0]["v_min"],
                    v_max=inv.mppt_windows[0]["v_max"],
                    count=inv.mppt_windows[0].get("count", 1),
                ),
            ),
            dc_series_count=7 if spec.targets.dc_kw_stc >= 5 else 8,
            ac_conductor=None,
            dc_ocpd=None,
            circuit_kind="ac_feeder",
        )
    )
    ops += _collect_ops(final)

    # 15) BOM (pull schedules if any)
    sched_data = {}
    for op in sch.operations:
        if op.op == "set_meta" and op.value.get("path") == "physical.schedules":
            sched_data = op.value.get("data", {})
            break
    bom = bom_tool.generate_bom(
        bom_tool.GenerateBOMInput(
            session_id=session_id,
            request_id=f"{request_id}:bom",
            bundles=[],
            schedules=sched_data,
            equip={
                "inverter": {"id": inv.id, "title": inv.title},
                "module": {"id": m.id, "title": m.title},
                "array_modules": 14 if spec.targets.dc_kw_stc >= 5 else 8,
            },
        )
    )
    ops += _collect_ops(bom)

    # 16) Story
    story = explain_design_v2.explain_design_v2(
        explain_design_v2.ExplainDesignV2Input(
            session_id=session_id,
            request_id=f"{request_id}:story",
            design_state={
                "env": {
                    "site_tmin_C": spec.env.site_tmin_C,
                    "site_tmax_C": spec.env.site_tmax_C,
                },
                "counts": {
                    "modules": 14 if spec.targets.dc_kw_stc >= 5 else 8,
                    "inverters": 1,
                },
            },
            audience="non-technical",
        )
    )
    ops += _collect_ops(story)

    return make_patch(request_id, ops)


def auto_design_from_nl(
    utterance: str, session_id: str, request_id: str, simulate: bool = True
) -> ODLPatch:
    """Parse a natural-language request and run Auto-Designer.

    This convenience wrapper first converts the ``utterance`` into a
    :class:`PlanSpec` via :func:`parse_plan_spec`, then executes
    :func:`run_auto_design`. Both patches are merged so callers can preview the
    stored specification alongside the design outputs.
    """

    # 1) Parse NL -> PlanSpec and persist the spec via meta patch
    parsed = parse_plan_spec(
        NLToPlanSpecInput(
            session_id=session_id,
            request_id=f"{request_id}:nl",
            utterance=utterance,
        )
    )
    spec = PlanSpec(**parsed["spec"])

    # 2) Run the auto designer (simulate by default for safety)
    ad_patch = run_auto_design(
        spec, session_id=session_id, request_id=f"{request_id}:ad", simulate=simulate
    )

    # 3) Merge ops so UI can preview both spec storage and design outputs
    merged_ops = parsed["patch"].operations + ad_patch.operations
    return make_patch(request_id, merged_ops)


__all__ = ["run_auto_design", "auto_design_from_nl"]

