# backend/tests/test_component_naming_policy.py
"""Tests for the component naming policy helper."""

import importlib.util
import os
import sys
from pathlib import Path

# ensure settings load with dummy environment variables
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from backend.config import settings  # noqa: E402

# Load the module directly to avoid importing backend.services.__init__
MODULE_PATH = ROOT / "backend" / "services" / "component_naming_policy.py"
spec = importlib.util.spec_from_file_location("component_naming_policy", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
get_naming_policy = module.get_naming_policy


def test_get_naming_policy_matches_settings() -> None:
    """Returned policy mirrors configuration values."""

    policy = get_naming_policy()

    assert policy["template"] == settings.component_name_template
    assert policy["version"] == settings.component_naming_version

