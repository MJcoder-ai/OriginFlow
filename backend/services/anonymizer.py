"""Simple anonymization utilities for prompts and contexts.

This module provides functions to redact personally identifiable
information (PII) from user prompts and design contexts before they
are embedded or stored.  For full PII detection, consider using
Microsoft Presidio, which offers `AnalyzerEngine` and
`AnonymizerEngine` to detect and mask sensitive entities such as
phone numbers, email addresses and names【582760942996744†L109-L142】.  Here we
implement a light-weight fallback based on regular expressions.
"""
from __future__ import annotations

import re
from typing import Any, Dict

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b\d{3}[- ]\d{3}[- ]\d{4}\b")


def anonymize(text: str) -> str:
    """Redact simple PII patterns from a string."""
    if not text:
        return text
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    return text


def anonymize_context(ctx: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Recursively anonymize string values in a context dictionary."""
    if ctx is None:
        return None
    def _mask(v: Any) -> Any:
        if isinstance(v, str):
            return anonymize(v)
        if isinstance(v, dict):
            return {k: _mask(val) for k, val in v.items()}
        if isinstance(v, list):
            return [_mask(item) for item in v]
        return v
    return _mask(ctx)
