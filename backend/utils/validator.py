"""Envelope validation utilities.

This module defines helper functions for validating standard
envelopes returned by agent templates and orchestrator components.
Validation ensures that required fields are present and that the
result structure matches the declared schema.  Later sprints may
extend this to perform JSON Schema checks and constraint evaluation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from backend.models.standard_envelope import StandardEnvelope


def validate_envelope(envelope: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a candidate envelope against the StandardEnvelope schema.

    Args:
        envelope: A dictionary representation of an envelope.

    Returns:
        A tuple ``(is_valid, errors)`` where ``is_valid`` is True if the
        envelope conforms to the schema and ``errors`` is a list of
        error messages describing validation failures.
    """
    errors: List[str] = []
    try:
        StandardEnvelope.model_validate(envelope)
    except Exception as exc:
        errors.append(str(exc))
        return False, errors
    return True, errors
