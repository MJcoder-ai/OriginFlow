from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class CompatibilityIssue(BaseModel):
    severity: Literal["info", "warning", "error"]
    category: str
    message: str
    suggested_solutions: List[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    issues: List[CompatibilityIssue] = Field(default_factory=list)


class CompatibilityReport(BaseModel):
    results: Dict[str, ValidationResult]

    def total_issues(self) -> int:
        return sum(len(r.issues) for r in self.results.values())


__all__ = ["CompatibilityIssue", "ValidationResult", "CompatibilityReport"]
