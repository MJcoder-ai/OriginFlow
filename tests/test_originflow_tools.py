import math
import pathlib
import importlib.util
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

# Stub backend.odl.schemas to avoid heavy dependencies during tests
import types

schemas_spec = importlib.util.spec_from_file_location(
    "backend.odl.schemas", ROOT / "backend/odl/schemas.py"
)
schemas_module = importlib.util.module_from_spec(schemas_spec)
schemas_spec.loader.exec_module(schemas_module)  # type: ignore
sys.modules.setdefault("backend", types.ModuleType("backend"))
backend_odl = types.ModuleType("backend.odl")
backend_odl.schemas = schemas_module  # type: ignore
sys.modules["backend.odl"] = backend_odl
sys.modules["backend.odl.schemas"] = schemas_module
backend_tools = types.ModuleType("backend.tools")
backend_tools.__path__ = [str(ROOT / "backend" / "tools")]
sys.modules.setdefault("backend.tools", backend_tools)

def _load(mod: str):
    path = ROOT / "backend" / "tools" / f"{mod}.py"
    name = f"backend.tools.{mod}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module

electrical = _load("electrical")
analysis = _load("analysis")
standards = _load("standards")
components = _load("components")
datasheets = _load("datasheets")
comm = _load("comm")

from backend.tools.schemas import (
    SelectDcStringingInput,
    PvModuleSpec,
    InverterSpec,
    InverterDcWindow,
    EnvProfile,
    SelectOcpDcInput,
    SelectOcpAcInput,
    BreakerCurve,
    BreakerSpec,
    ApplyBreakerCurveInput,
    SelectConductorsInput,
    ConductorEnv,
    CalcVdropInput,
    CalcIfaultInput,
    ExpandConnectionsInput,
    CheckComplianceInput,
    EnrichComponentMetadataInput,
    IngestComponentJsonInput,
    LinkBudgetPlannerInput,
)


SESSION = "s"


def test_dc_stringing_basic():
    inp = SelectDcStringingInput(
        session_id=SESSION,
        request_id="r1",
        module=PvModuleSpec(voc_stc=40, isc_stc=10, vmp=32, imp=9, beta_voc_pct_per_C=-0.28),
        inverter=InverterSpec(dc_windows=[InverterDcWindow(v_min=200, v_max=800, mppt_count=2)], max_system_vdc=600),
        env=EnvProfile(ambient_min_C=-10, ambient_max_C=50),
        desired_module_count=20,
    )
    patch = electrical.select_dc_stringing(inp)
    assert any(op.value["id"].startswith("ann:dc_stringing") for op in patch.operations)


def test_ocp_dc():
    inp = SelectOcpDcInput(session_id=SESSION, request_id="r2", isc_stc_per_string=10, n_parallel_strings=4)
    patch = electrical.select_ocp_dc(inp)
    ann = [op for op in patch.operations if op.value["id"].startswith("ann:ocp_dc")][0]
    assert ann.value["attrs"]["decision"]["fuse_required"] is True


def test_ocp_ac():
    curve = BreakerCurve(points=[(3, 100), (5, 10), (10, 0.5)])
    lib = [BreakerSpec(rating_A=25, frame_A=25, curve=curve, voltage=480, poles=2, series_sc_rating_ka=22)]
    inv = InverterSpec(dc_windows=[], max_system_vdc=600, ac_inom_A=20)
    inp = SelectOcpAcInput(session_id=SESSION, request_id="r3", inverter=inv, breaker_library=lib)
    patch = electrical.select_ocp_ac(inp)
    assert any(op.value["id"].startswith("ac_breaker") for op in patch.operations)


def test_breaker_curve():
    curve = BreakerCurve(points=[(3, 100), (5, 10), (10, 0.5)])
    inp = ApplyBreakerCurveInput(session_id=SESSION, request_id="r4", breaker_curve=curve, current_multiple=5)
    patch = analysis.apply_breaker_curve(inp)
    val = patch.operations[0].value["attrs"]["result"]["t_trip_s"]
    assert 1 < val < 20


def test_conductor_selection_and_vdrop():
    env = ConductorEnv(length_m=30, max_vdrop_pct=3)
    inp = SelectConductorsInput(session_id=SESSION, request_id="r5", current_A=20, system_v=480, env=env)
    patch = electrical.select_conductors(inp)
    ann = patch.operations[0].value["attrs"]["decision"]["choice"]
    assert float(ann["ampacity_A"]) >= 20
    vd_inp = CalcVdropInput(session_id=SESSION, request_id="r6", current_A=20, system_v=480, phase="3ph", R_ohm_per_km=0.2, length_m=30)
    vpatch = analysis.calculate_voltage_drop(vd_inp)
    assert vpatch.operations[0].value["attrs"]["result"]["v_drop_V"] > 0


def test_fault_current():
    inp = CalcIfaultInput(session_id=SESSION, request_id="r7", dc_isc_stc=10, dc_parallel_strings=3, ac_inverter_inom=20)
    patch = analysis.calculate_fault_current(inp)
    attrs = patch.operations[0].value["attrs"]["result"]
    assert attrs["dc_fault_A"] == 37.5
    assert attrs["ac_fault_A"] == 24.0


def test_expand_and_compliance():
    epatch = electrical.expand_connections(ExpandConnectionsInput(session_id=SESSION, request_id="r8", source_id="a", target_id="b"))
    assert len(epatch.operations) >= 3
    cpatch = standards.check_compliance(
        CheckComplianceInput(
            session_id=SESSION,
            request_id="r9",
            env=EnvProfile(ambient_min_C=-10, ambient_max_C=50),
            module=PvModuleSpec(voc_stc=40, isc_stc=10, vmp=32, imp=9, beta_voc_pct_per_C=-0.28),
            inverter=InverterSpec(dc_windows=[], max_system_vdc=1000),
            dc_series_count=30,
        )
    )
    assert cpatch.operations[0].value["attrs"]["result"]["findings"]


def test_components_datasheets_comm():
    enrich = components.enrich_component_metadata(
        EnrichComponentMetadataInput(session_id=SESSION, request_id="r10", existing_json={"id": "x"}, new_attrs={"a": 1}, provenance={"src": "test"})
    )
    assert enrich.operations[0].value["attrs"]["component_json"]["a"] == 1
    ingest = datasheets.ingest_component_json(
        IngestComponentJsonInput(session_id=SESSION, request_id="r11", raw={"Voc": 50}, mapping={"Voc": "voc_stc"})
    )
    assert ingest.operations[0].value["attrs"]["component_json"]["voc_stc"] == 50
    link = comm.link_budget_planner(LinkBudgetPlannerInput(session_id=SESSION, request_id="r12", topology="rs485_multi_drop", device_count=5, segment_length_m=1500))
    assert link.operations[0].value["attrs"]["ok"] is False

