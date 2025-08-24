from backend.tools.select_equipment import select_equipment, SelectEquipmentInput
from backend.tools.stringing import (
    select_dc_stringing,
    SelectStringingInput,
    Env,
    Module,
    Inverter,
    MpptWindow,
)


def test_select_equipment_picks_reasonable_models():
    patch = select_equipment(SelectEquipmentInput(session_id="s", request_id="r", target_kw_stc=3.0))
    ops = patch.operations
    assert any(op.op == "set_meta" and op.value.get("path") == "design_state.equip" for op in ops)


def test_stringing_respects_voltage_and_mppt():
    m = Module(p_W=400, voc=49.5, vmp=41.5, imp=10.7, beta_voc_pct_per_C=-0.28)
    inv = Inverter(max_system_vdc=600, mppt_windows=[MpptWindow(v_min=200, v_max=550, count=2)])
    patch = select_dc_stringing(
        SelectStringingInput(
            session_id="s",
            request_id="r2",
            target_kw_stc=5.0,
            env=Env(site_tmin_C=-10),
            module=m,
            inverter=inv,
        )
    )
    ann = [op for op in patch.operations if op.op == "add_edge"][0]
    assert "N=" in ann.value["attrs"]["summary"]

