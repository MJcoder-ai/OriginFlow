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

    This function first attempts to validate the envelope using the
    Pydantic ``StandardEnvelope`` model.  If the model validation
    passes, additional manual checks ensure that required keys are
    present in the envelope and that the types of certain fields are
    appropriate.  Validation errors are collected and returned.

    Args:
        envelope: A dictionary representation of an envelope.

    Returns:
        A tuple ``(is_valid, errors)`` where ``is_valid`` is True if the
        envelope conforms to the schema and ``errors`` is a list of
        error messages describing validation failures.
    """
    errors: List[str] = []
    # Perform Pydantic model validation
    try:
        StandardEnvelope.model_validate(envelope)
    except Exception as exc:
        errors.append(str(exc))
    # Additional manual field checks
    required_keys = ["status", "result", "card", "metrics"]
    for key in required_keys:
        if key not in envelope:
            errors.append(f"Missing required field '{key}' in envelope")
    # Ensure metrics is a dictionary
    if "metrics" in envelope and not isinstance(envelope.get("metrics"), dict):
        errors.append("'metrics' field must be a dictionary")
    # Ensure errors and validations are lists if present
    for list_key in ["errors", "validations"]:
        if list_key in envelope and not isinstance(envelope.get(list_key), list):
            errors.append(f"'{list_key}' field must be a list")
    return (len(errors) == 0), errors
