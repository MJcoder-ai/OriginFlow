from backend.planner.pv_planner import plan_pv_single_line

def _find(tasks, comp, key='component_type'):
    return next(t for t in tasks if t['id'] == 'make_placeholders' and t['args'][key] == comp)

def test_three_kw_uses_one_inverter_and_eight_panels():
    plan = plan_pv_single_line('design a 3 kW PV system with 400 W modules')
    inv = _find(plan['tasks'], 'inverter')
    pan = _find(plan['tasks'], 'panel')
    assert inv['args']['count'] == 1
    assert pan['args']['count'] == 8

def test_400w_not_400_inverters():
    plan = plan_pv_single_line('add equipment: 400 W modules; design size ~5 kW')
    inv = _find(plan['tasks'], 'inverter')
    assert inv['args']['count'] == 1

def test_default_when_no_size():
    plan = plan_pv_single_line('please start a pv design')
    pan = _find(plan['tasks'], 'panel')
    assert pan['args']['count'] == 8
    assert 'defaulting panels' in ' '.join(plan.get('warnings', [])).lower()
