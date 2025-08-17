# backend/tests/test_component_naming_service.py
"""Tests for the ComponentNamingService."""

import importlib.util
import os
import sys
from pathlib import Path

# ensure settings load with dummy environment variables
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from backend.config import settings  # noqa: E402,F401

# Load the service module directly to avoid importing backend.services.__init__
MODULE_PATH = ROOT / "backend" / "services" / "component_naming_service.py"
spec = importlib.util.spec_from_file_location("component_naming_service", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
ComponentNamingService = module.ComponentNamingService


def test_generate_name_basic() -> None:
    """Generates name using default template and power rating."""

    metadata = {
        "manufacturer": "Acme",
        "part_number": "ZX-1",
        "power": "500 W",
        "category": "Inverter",
    }

    expected = "Acme ZX-1 - 500 W Inverter"
    assert ComponentNamingService.generate_name(metadata) == expected


def test_generate_name_rating_fallback() -> None:
    """Falls back to capacity when power is missing."""

    metadata = {
        "manufacturer": "FooCorp",
        "part_number": "B-2",
        "capacity": "10 kWh",
    }

    template = "{manufacturer} {part_number} {rating}"
    name = ComponentNamingService.generate_name(metadata, template=template)
    assert name == "FooCorp B-2 10 kWh"

