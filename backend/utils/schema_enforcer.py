"""
Contract‑first schema enforcement for OriginFlow agent outputs.

This module defines a JSON schema for the standard ADPF envelope returned
by agents and provides a helper function to validate envelopes at
runtime.  The goal is to ensure that all agent responses conform to
their declared output structure before they are consumed by the
orchestrator or downstream components.

The schema enforces the following structure:

* Top‑level object with required keys ``thought``, ``output`` and
  ``status``.
* ``thought`` must be a string describing the agent’s internal
  reasoning.
* ``output`` must be an object containing at least a ``card`` and
  optionally a ``patch``; additional properties are allowed.
* ``status`` must be one of ``complete``, ``pending`` or
  ``blocked``.
* ``warnings`` is optional and, if present, must be a list of strings
  or null.

Additional keys are permitted at both the top level and within
``output`` so that agents can extend the envelope with domain‑specific
fields (e.g. ``selected_card`` in the consensus agent).  The schema
does not validate the internal structure of ``card`` or ``patch``
because these vary across agents; however, agents are encouraged to
document and validate their own card and patch schemas separately.
"""

from __future__ import annotations

from typing import Any, Dict

import jsonschema


# JSON Schema defining the ADPF envelope structure.
ADPF_ENVELOPE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["thought", "output", "status"],
    "properties": {
        "thought": {"type": "string"},
        "output": {
            "type": "object",
            "required": ["card"],
            "properties": {
                "card": {"type": "object"},
                "patch": {"type": ["object", "null"]},
            },
            "additionalProperties": True,
        },
        "status": {"type": "string", "enum": ["complete", "pending", "blocked"]},
        "warnings": {
            "type": ["array", "null"],
            "items": {"type": "string"},
        },
    },
    "additionalProperties": True,
}


def validate_envelope(envelope: Dict[str, Any]) -> None:
    """Validate an agent response envelope against the ADPF schema.

    This function uses jsonschema to validate the provided dictionary
    against the ``ADPF_ENVELOPE_SCHEMA``.  If validation fails, a
    ``jsonschema.exceptions.ValidationError`` is raised.

    Args:
        envelope: The agent response to validate.

    Raises:
        jsonschema.exceptions.ValidationError: If the envelope does not
            conform to the schema.
    """
    jsonschema.validate(instance=envelope, schema=ADPF_ENVELOPE_SCHEMA)

