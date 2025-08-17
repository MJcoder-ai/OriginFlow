import os
import sys
from pathlib import Path
import importlib.util

import pytest

# Set defaults for environment variables used by the backend
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Add repository root to sys.path so modules can be imported
sys.path.append(str(Path(__file__).resolve().parents[2]))


def load_nlp_service():
    spec = importlib.util.spec_from_file_location(
        "nlp_service",
        Path(__file__).resolve().parents[1] / "services" / "nlp_service.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_parse_command_extracts_power():
    nlp_service = load_nlp_service()
    parse_command = nlp_service.parse_command
    res = parse_command("design a 5 kW solar system")
    assert "target_power" in res
    assert abs(res["target_power"] - 5000) < 1e-3


def test_parse_command_extracts_panel_count():
    nlp_service = load_nlp_service()
    parse_command = nlp_service.parse_command
    res = parse_command("add 6 panels to the design")
    assert res.get("panel_count") == 6


def test_parse_command_domain_inference():
    nlp_service = load_nlp_service()
    parse_command = nlp_service.parse_command
    pv = parse_command("design solar pv system")
    assert pv.get("domain") == "pv"
    hvac = parse_command("install new HVAC unit")
    assert hvac.get("domain") == "hvac"
