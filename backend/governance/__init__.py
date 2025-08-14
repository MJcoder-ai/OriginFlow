"""Governance layer for ADPF 2.1.

This package exposes utilities to enforce platform policies such as
budgets, safety rules and telemetry requirements.  The initial
implementation provides a minimal stub used by the
`DynamicPromptOrchestratorV2`.
"""

from .governance import Governance  # noqa: F401

__all__ = ["Governance"]
