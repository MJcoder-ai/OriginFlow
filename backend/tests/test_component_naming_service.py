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
spec = importlib.util.spec_from_file_location(
    "component_naming_service", MODULE_PATH
)
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


def test_generate_name_review_flag_when_missing_fields() -> None:
    """Returns a review flag when manufacturer or part number is missing."""

    metadata = {
        "manufacturer": "",  # missing
        "part_number": "",  # missing
        "category": "Inverter",
    }

    name, needs_review = ComponentNamingService.generate_name(
        metadata, return_review_flag=True
    )

    assert name == "- Inverter"
    assert needs_review is True


def test_generate_name_complete_metadata_no_review_flag() -> None:
    """Complete metadata should not trigger a review flag."""

    metadata = {
        "manufacturer": "Trina",
        "part_number": "TSM-425DE09R.08",
        "power": "425 W",
        "category": "Panel",
    }

    name, needs_review = ComponentNamingService.generate_name(
        metadata, return_review_flag=True
    )

    assert name == "Trina TSM-425DE09R.08 - 425 W Panel"
    assert needs_review is False


def test_generate_name_missing_manufacturer() -> None:
    """Missing manufacturer should prefix with part number and flag review."""

    metadata = {
        "part_number": "ABC123",
        "category": "Inverter",
        "power": 10,
    }

    name, needs_review = ComponentNamingService.generate_name(
        metadata, return_review_flag=True
    )

    assert name.startswith("ABC123")
    assert needs_review is True


def test_generate_name_unknown_placeholder_is_ignored() -> None:
    """Unknown placeholders in templates are removed gracefully."""

    metadata = {
        "manufacturer": "LG",
        "part_number": "RESU10H",
        "category": "Battery",
        "capacity": "9.8 kWh",
    }
    template = "{manufacturer} {part_number} {unknown} - {rating} {category}"

    name = ComponentNamingService.generate_name(metadata, template=template)

    assert "{unknown}" not in name
    assert name == "LG RESU10H - 9.8 kWh Battery"
