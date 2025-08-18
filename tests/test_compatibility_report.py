import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import importlib.util

spec = importlib.util.spec_from_file_location(
    "compatibility", ROOT / "backend" / "services" / "compatibility.py"
)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

CompatibilityIssue = module.CompatibilityIssue
CompatibilityReport = module.CompatibilityReport
ValidationResult = module.ValidationResult


def test_total_issues_counts_all() -> None:
    issue = CompatibilityIssue(severity="error", category="x", message="oops")
    report = CompatibilityReport(
        results={
            "electrical": ValidationResult(issues=[issue]),
            "mechanical": ValidationResult(issues=[]),
            "thermal": ValidationResult(issues=[issue, issue]),
            "communication": ValidationResult(issues=[]),
        }
    )
    assert report.total_issues() == 3


def test_legacy_constructor_rejected() -> None:
    issue = CompatibilityIssue(severity="error", category="x", message="oops")
    with pytest.raises(ValidationError):
        CompatibilityReport(
            electrical=ValidationResult(issues=[issue]),
            mechanical=ValidationResult(issues=[]),
            thermal=ValidationResult(issues=[]),
            communication=ValidationResult(issues=[]),
        )
