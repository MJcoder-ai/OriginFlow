# backend/services/compatibility.py
"""Compatibility validation service for OriginFlow.

This module defines a skeleton implementation of a multi-domain
compatibility engine.  A future version will perform electrical,
mechanical, thermal and communication rule checks across all
components and connections in a design.  For now it provides a
scaffold that always returns successful validation results, allowing
the API and calling code to be integrated without blocking on rule
implementation.

The compatibility engine operates on a ``DesignSnapshot``, converting
the graph into a component map and connection list.  Each category
of rules is encapsulated in its own class, enabling targeted
validation and easy extension in future releases.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CompatibilityIssue(BaseModel):
    """Represents a single compatibility issue.

    Attributes:
        severity: A string indicating the severity of the issue (e.g.
            ``"error"``, ``"warning"``).
        category: A short category name (e.g. ``"voltage_mismatch"``).
        message: A human-readable description of the problem.
        suggested_solutions: Optional list of suggestions to fix the issue.
    """

    severity: str
    category: str
    message: str
    suggested_solutions: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Container for issues produced by a single rule category."""

    issues: list[CompatibilityIssue]

    def is_ok(self) -> bool:
        """Return ``True`` when no issues are present."""

        return len(self.issues) == 0


class CompatibilityReport(BaseModel):
    """Aggregated results across multiple rule categories."""

    results: dict[str, ValidationResult]

    def total_issues(self) -> int:
        """Return the total number of issues across all categories."""

        return sum(len(result.issues) for result in self.results.values())


class ElectricalCompatibilityRules:
    """Stub rule set for electrical compatibility.

    A future implementation will check voltage, current and connector
    specifications between components.  At present this method
    performs no checks and returns an empty ``ValidationResult``.
    """

    async def validate(
        self,
        components: dict[str, Any],
        connections: list[dict[str, str]],
    ) -> ValidationResult:
        # TODO: implement electrical validation logic
        return ValidationResult(issues=[])


class MechanicalCompatibilityRules:
    """Stub rule set for mechanical compatibility.

    To be extended with checks for mounting compatibility, weight
    limits, and physical form factors.  Currently returns no issues.
    """

    async def validate(
        self,
        components: dict[str, Any],
        connections: list[dict[str, str]],
    ) -> ValidationResult:
        # TODO: implement mechanical validation logic
        return ValidationResult(issues=[])


class ThermalCompatibilityRules:
    """Stub rule set for thermal compatibility.

    When implemented, this class will ensure that components
    dissipate heat appropriately and are rated for operating
    temperatures.  Returns no issues for now.
    """

    async def validate(
        self,
        components: dict[str, Any],
        connections: list[dict[str, str]],
    ) -> ValidationResult:
        # TODO: implement thermal validation logic
        return ValidationResult(issues=[])


class CommunicationCompatibilityRules:
    """Stub rule set for communication protocol compatibility.

    Future checks may include verifying bus standards, connector
    compatibility and data rates.  Currently returns no issues.
    """

    async def validate(
        self,
        components: dict[str, Any],
        connections: list[dict[str, str]],
    ) -> ValidationResult:
        # TODO: implement communication validation logic
        return ValidationResult(issues=[])


class CompatibilityEngine:
    """High-level compatibility validation orchestrator.

    The engine delegates validation to specific rule classes and
    aggregates their results into a single report.  This skeleton
    implementation leaves the actual rule logic to be developed.
    """

    def __init__(self) -> None:
        self.rules = {
            "electrical": ElectricalCompatibilityRules(),
            "mechanical": MechanicalCompatibilityRules(),
            "thermal": ThermalCompatibilityRules(),
            "communication": CommunicationCompatibilityRules(),
        }
        # Cache of previous validation results keyed by (session_id, version)
        self._cache: dict[tuple[str, int], CompatibilityReport] = {}

    async def validate_system_compatibility(self, snapshot: "DesignSnapshot") -> CompatibilityReport:
        """Validate all compatibility rules against a design snapshot.

        Args:
            snapshot: A design snapshot containing components and links.

        Returns:
            A ``CompatibilityReport`` summarising validation results across
            all rule categories.
        """

        # Attempt to return cached result when session and version are provided
        if snapshot.session_id and snapshot.version:
            cache_key = (snapshot.session_id, snapshot.version)
            cached = self._cache.get(cache_key)
            if cached:
                return cached

        # Local import to avoid circular dependencies
        from backend.schemas.analysis import DesignSnapshot  # noqa: F401

        # Convert snapshot into mapping and connection list
        components: dict[str, Any] = {comp.id: comp for comp in snapshot.components}
        connections: list[dict[str, str]] = [
            {"source_id": link.source_id, "target_id": link.target_id}
            for link in snapshot.links
        ]

        results: dict[str, ValidationResult] = {}
        for name, rule in self.rules.items():
            try:
                result = await rule.validate(components, connections)
            except Exception as exc:  # pragma: no cover - defensive
                issue = CompatibilityIssue(
                    severity="error",
                    category="rule_failure",
                    message=f"{name} rule failed: {exc}",
                    suggested_solutions=[],
                )
                result = ValidationResult(issues=[issue])
            results[name] = result

        report = CompatibilityReport(results=results)

        if snapshot.session_id and snapshot.version:
            cache_key = (snapshot.session_id, snapshot.version)
            self._cache[cache_key] = report

        return report


CompatibilityIssue.model_rebuild()
ValidationResult.model_rebuild()
CompatibilityReport.model_rebuild()
