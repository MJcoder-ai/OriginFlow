import os
import sys
from pathlib import Path
import importlib.util

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

repo_root = Path(__file__).resolve().parents[2]
sys.path.append(str(repo_root))

import pytest
from fastapi import HTTPException

# Load AnalyzeOrchestrator without importing backend.services package
spec = importlib.util.spec_from_file_location(
    "analyze_service", repo_root / "backend" / "services" / "analyze_service.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
AnalyzeOrchestrator = mod.AnalyzeOrchestrator

from backend.agents.component_agent import component_agent  # ensure spec


def test_auto_standard_code_generated():
    orch = AnalyzeOrchestrator()
    actions = orch._validate_actions(
        [
            {
                "action": "add_component",
                "payload": {"name": "Panel", "type": "panel"},
            }
        ]
    )
    assert actions[0].payload["standard_code"].startswith("AUTO-")


def test_invalid_component_payload_returns_422():
    orch = AnalyzeOrchestrator()
    with pytest.raises(HTTPException) as exc:
        orch._validate_actions(
            [
                {
                    "action": "add_component",
                    "payload": {"type": "panel"},  # missing name
                }
            ]
        )
    assert exc.value.status_code == 422
