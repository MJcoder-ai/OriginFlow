import math
import pytest

from backend.planner.parser import parse_design_command


def test_parse_defaults_when_no_numbers():
    plan = parse_design_command("design a small solar pv system")
    assert plan.target_kw == 5.0  # default
    assert plan.panel_watts == 400  # default
    assert plan.layer == "electrical"  # default
    assert plan.panel_count == math.ceil(5000 / 400)
    assert plan.assumptions["defaulted_target_kw"] is True
    assert plan.assumptions["defaulted_panel_watts"] is True
    assert plan.assumptions["defaulted_layer"] is True


def test_parse_kw_and_panel_watts_and_layer():
    plan = parse_design_command(
        "please design a 7.5kW PV with 425 W panels on single-line diagram"
    )
    assert plan.target_kw == 7.5
    assert plan.panel_watts == 425
    assert plan.layer == "single-line"
    assert plan.panel_count == math.ceil(7500 / 425)
    assert plan.assumptions["defaulted_target_kw"] is False
    assert plan.assumptions["defaulted_panel_watts"] is False
    assert plan.assumptions["defaulted_layer"] is False


@pytest.mark.parametrize(
    "text,expected_kw",
    [
        ("design a 10 kW system", 10.0),
        ("Design 3.2KW rooftop array", 3.2),
        ("we need 12kw farm", 12.0),
    ],
)
def test_kw_regex_variants(text, expected_kw):
    plan = parse_design_command(text)
    assert plan.target_kw == expected_kw


def test_panel_watts_ignored_if_no_panel_keyword():
    plan = parse_design_command(
        "design 5kW using 500 W inverter"
    )  # wattage present but not 'panel'
    assert plan.panel_watts == 400  # default
    assert plan.panel_count == math.ceil(5000 / 400)
