from backend.tools.design_state import (
    compute_design_state,
    ComputeDesignStateInput,
    Env,
    Module,
    Inverter,
    InverterWindow,
)
from backend.tools.standards_check_v2 import (
    check_compliance_v2,
    CheckComplianceV2Input,
    Env as CEnv,
    Module as CModule,
    Inverter as CInv,
    MPPT,
    ConductorChoice,
    OCPD,
)


SESSION = "test"


def test_design_state_persists_meta_and_ann():
    inp = ComputeDesignStateInput(
        session_id=SESSION,
        request_id="ds1",
        env=Env(site_tmin_C=-10, site_tmax_C=45, code_profile="NEC_2023"),
        modules=[
            Module(
                id="M1",
                voc_stc=49.5,
                vmp=41.0,
                isc_stc=11.0,
                imp=10.4,
                beta_voc_pct_per_C=-0.28,
            )
        ],
        inverters=[
            Inverter(
                id="INV1",
                max_system_vdc=1000,
                windows=[InverterWindow(v_min=350, v_max=800, count=2)],
                ac_inom_A=80.0,
            )
        ],
    )
    patch = compute_design_state(inp)
    ops = patch.operations
    assert any(op.op == "set_meta" and op.value["path"] == "design_state" for op in ops)
    assert any(op.op == "add_edge" and op.value["id"].startswith("ann:design_state:") for op in ops)


def test_compliance_v2_flags_overvoltage_and_mppt():
    env = CEnv(site_tmin_C=-20, site_tmax_C=45, code_profile="NEC_2023")
    m = CModule(voc_stc=50.0, vmp=41.0, isc_stc=10.0, beta_voc_pct_per_C=-0.30)
    inv = CInv(max_system_vdc=600, mppt=MPPT(v_min=300, v_max=450, count=2))
    ci = CheckComplianceV2Input(
        session_id=SESSION,
        request_id="cc1",
        env=env,
        module=m,
        inverter=inv,
        dc_series_count=16,
    )
    patch = check_compliance_v2(ci)
    findings = patch.operations[0].value["attrs"]["result"]["findings"]
    assert any(f["code"] == "DC_MAX_V" and f["severity"] == "error" for f in findings)
    assert any(f["code"] == "MPPT_WINDOW" for f in findings)


def test_compliance_v2_ampacity_and_vdrop():
    env = CEnv(site_tmin_C=-10, site_tmax_C=45, code_profile="NEC_2023")
    ci = CheckComplianceV2Input(
        session_id=SESSION,
        request_id="cc2",
        env=env,
        ac_conductor=ConductorChoice(size="6AWG", ampacity_A=50, vdrop_pct=4.0),
        dc_ocpd=OCPD(rating_A=60),
        circuit_kind="ac_feeder",
    )
    patch = check_compliance_v2(ci)
    findings = patch.operations[0].value["attrs"]["result"]["findings"]
    assert any(f["code"] == "AMPACITY_LT_OCPD" and f["severity"] == "error" for f in findings)
    assert any(f["code"] == "VOLTAGE_DROP" for f in findings)

