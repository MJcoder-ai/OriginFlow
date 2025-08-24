"""
Typed schemas for tool inputs/outputs.

Tools are **pure**: they take typed inputs (small ODL slices + params) and
return typed outputs (usually an ODLPatch). They never talk to the DB or the
ODL store directly. The orchestrator composes tools and applies returned
patches via the ODL API.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

from backend.odl.schemas import ODLNode, ODLEdge, ODLGraph, ODLPatch, PatchOp


# ---------- Shared ----------


class ToolBase(BaseModel):
    """Base fields common to tool requests."""

    session_id: str = Field(..., description="Design session id")
    request_id: str = Field(..., description="Idempotency scope for op_ids")
    model_config = ConfigDict(extra="forbid")


# ---------- Selection ----------


class ComponentCandidate(BaseModel):
    part_number: str
    name: str
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    power: Optional[float] = None
    price: Optional[float] = None
    score: Optional[float] = Field(None, description="Ranking score (higher is better)")


class SelectionInput(ToolBase):
    placeholder_type: str = Field(
        ..., description="e.g., generic_panel, generic_inverter"
    )
    requirements: Dict[str, float] = Field(
        default_factory=dict, description="Structured requirements (e.g., target_power)"
    )
    pool: List[Dict] = Field(
        default_factory=list, description="Candidate component dicts from library"
    )


class SelectionResult(BaseModel):
    candidates: List[ComponentCandidate]


# ---------- Wiring ----------


class GenerateWiringInput(ToolBase):
    view_nodes: List[ODLNode] = Field(
        default_factory=list, description="Nodes visible in the current layer/view"
    )
    edge_kind: str = Field("electrical")


# ---------- Structural ----------


class GenerateMountsInput(ToolBase):
    view_nodes: List[ODLNode] = Field(default_factory=list)
    mount_type: str = Field("mount")
    layer: str = Field("structural")


# ---------- Monitoring ----------


class AddMonitoringInput(ToolBase):
    view_nodes: List[ODLNode] = Field(default_factory=list)
    device_type: str = Field("monitoring")
    layer: str = Field("electrical")


# ---------- Placeholders ----------


class MakePlaceholdersInput(ToolBase):
    count: int = Field(1, ge=1)
    placeholder_type: str = Field(
        ..., description="generic_panel | generic_inverter | ..."
    )
    attrs: Dict[str, object] = Field(default_factory=dict)


# ---------- Deletion ----------


class DeleteNodesInput(ToolBase):
    view_nodes: List[ODLNode] = Field(default_factory=list)
    component_types: List[str] = Field(default_factory=list, description="Types to delete")


# ---------- Consensus ----------


class RankInput(BaseModel):
    candidates: List[ComponentCandidate]
    objective: Literal["max_score", "min_price", "best_value"] = "max_score"


class RankResult(BaseModel):
    candidates: List[ComponentCandidate]


# ---------- Helpers ----------


def make_patch(request_id: str, ops: List[PatchOp]) -> ODLPatch:
    """Create an ODLPatch with a deterministic patch_id from request_id."""

    return ODLPatch(patch_id=f"patch:{request_id}", operations=ops)


# ---------- Electrical & Analysis ----------


class EnvProfile(BaseModel):
    """Site environment bounds for electrical calculations."""

    ambient_min_C: float = Field(..., description="Lowest ambient temperature")
    ambient_max_C: float = Field(..., description="Highest ambient temperature")
    elevation_m: float | None = Field(
        None, description="Site elevation for optional corrections"
    )


class PvModuleSpec(BaseModel):
    """Minimal PV module electrical specification."""

    voc_stc: float
    isc_stc: float
    vmp: float
    imp: float
    beta_voc_pct_per_C: float = Field(
        ..., description="Voc temperature coefficient (%/°C, negative)"
    )


class InverterDcWindow(BaseModel):
    v_min: float
    v_max: float
    mppt_count: int = 1


class InverterSpec(BaseModel):
    """Inverter side parameters required for stringing/OCPD."""

    dc_windows: List[InverterDcWindow] = Field(default_factory=list)
    max_system_vdc: float = 1000.0
    ac_v_ll: float | None = None
    ac_phase: Literal["1", "3"] = "3"
    ac_freq_hz: int = 50
    ac_inom_A: float | None = None
    ifault_multiplier: float = Field(1.2, description="Fault current multiple")


class BreakerCurve(BaseModel):
    """Time–current characteristic as list of (multiple, seconds)."""

    points: List[tuple[float, float]]


class BreakerSpec(BaseModel):
    rating_A: int
    frame_A: int
    curve: BreakerCurve
    voltage: float
    poles: int
    series_sc_rating_ka: float


class ConductorEnv(BaseModel):
    material: Literal["Cu", "Al"] = "Cu"
    insulation: Literal["THHN", "XHHW", "PVC", "XLPE"] = "THHN"
    installation: Literal["conduit", "tray", "free_air"] = "conduit"
    current_carrying: int = Field(
        2, description="Number of current-carrying conductors in the raceway"
    )
    length_m: float = 10.0
    max_vdrop_pct: float = 3.0


class ConductorChoice(BaseModel):
    size_awg_or_kcmil: str
    qty_per_phase: int = 1
    vdrop_pct: float
    ampacity_A: float


# ---------- Tool inputs ----------


class SelectDcStringingInput(ToolBase):
    view_nodes: List[ODLNode] = Field(default_factory=list)
    module: PvModuleSpec
    inverter: InverterSpec
    env: EnvProfile
    desired_module_count: int
    parallel_limit: int = 12
    series_margin_pct: float = 0.97


class SelectOcpDcInput(ToolBase):
    view_nodes: List[ODLNode] = Field(default_factory=list)
    isc_stc_per_string: float
    n_parallel_strings: int
    cont_factor: float = 1.25
    fuse_catalog_A: List[int] = Field(default_factory=lambda: [10, 15, 20, 25, 30])
    require_fusing_if_parallel_gt: int = 2


class SelectOcpAcInput(ToolBase):
    view_nodes: List[ODLNode] = Field(default_factory=list)
    inverter: InverterSpec
    breaker_library: List[BreakerSpec]
    cont_factor: float = 1.25
    min_sc_rating_ka: float = 10.0


class ApplyBreakerCurveInput(ToolBase):
    breaker_curve: BreakerCurve
    current_multiple: float


class SelectConductorsInput(ToolBase):
    view_nodes: List[ODLNode] = Field(default_factory=list)
    current_A: float
    system_v: float
    phase: Literal["dc", "1ph", "3ph"] = "dc"
    env: ConductorEnv
    resistivity_ohm_km: Dict[str, float] = Field(
        default_factory=lambda: {"Cu": 0.018, "Al": 0.029}
    )
    ampacity_table_A: Dict[str, float] = Field(
        default_factory=lambda: {
            "14AWG": 20,
            "12AWG": 25,
            "10AWG": 35,
            "8AWG": 50,
            "6AWG": 65,
            "4AWG": 85,
            "2AWG": 115,
            "1/0": 150,
            "2/0": 175,
            "3/0": 200,
            "4/0": 230,
        }
    )
    derate_ambient_pct: float = 1.0
    derate_bundling_pct: float = 1.0


class CalcVdropInput(ToolBase):
    current_A: float
    system_v: float
    phase: Literal["dc", "1ph", "3ph"]
    R_ohm_per_km: float
    length_m: float


class CalcIfaultInput(ToolBase):
    dc_isc_stc: float | None = None
    dc_parallel_strings: int | None = None
    dc_multiplier: float = 1.25
    ac_inverter_inom: float | None = None
    ac_fault_multiple: float = 1.2


class ExpandConnectionsInput(ToolBase):
    source_id: str
    target_id: str
    connection_type: Literal["dc_pv", "ac_3ph_4w", "ac_1ph_2w", "rs485"] = "dc_pv"
    add_ground: bool = True


class CheckComplianceInput(ToolBase):
    env: EnvProfile
    module: PvModuleSpec | None = None
    inverter: InverterSpec | None = None
    dc_series_count: int | None = None
    profile: Literal["NEC_2023", "IEC_60364", "AS_NZS_3000"] = "NEC_2023"


class EnrichComponentMetadataInput(ToolBase):
    existing_json: Dict[str, object] = Field(default_factory=dict)
    new_attrs: Dict[str, object] = Field(default_factory=dict)
    provenance: Dict[str, str] = Field(default_factory=dict)


class IngestComponentJsonInput(ToolBase):
    raw: Dict[str, object]
    mapping: Dict[str, str] = Field(default_factory=dict)


class LinkBudgetPlannerInput(ToolBase):
    topology: Literal["rs485_multi_drop", "ethernet_star"] = "rs485_multi_drop"
    device_count: int
    segment_length_m: float
    baud: int = 9600

