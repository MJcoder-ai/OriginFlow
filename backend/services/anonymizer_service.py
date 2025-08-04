"""Simple anonymization utilities for prompts and contexts.

This module provides :class:`AnonymizerService` which can redact
personally identifiable information (PII) such as emails and phone
numbers from arbitrary strings or nested dictionary contexts.  It uses
light-weight regular expressions as a fallback and avoids any global
state so the service can be safely instantiated per process.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional


class AnonymizerService:
    """Redact basic PII patterns from text and dictionaries."""

    EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    PHONE_RE = re.compile(r"\b\d{3}[- ]\d{3}[- ]\d{4}\b")

    def anonymize(self, text: str) -> str:
        """Redact simple PII patterns from a string."""
        if not text:
            return text
        text = self.EMAIL_RE.sub("[EMAIL]", text)
        text = self.PHONE_RE.sub("[PHONE]", text)
        return text

    def anonymize_context(self, ctx: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Recursively anonymize string values in a context dictionary."""
        if ctx is None:
            return None

        def _mask(v: Any) -> Any:
            if isinstance(v, str):
                return self.anonymize(v)
            if isinstance(v, dict):
                return {k: _mask(val) for k, val in v.items()}
            if isinstance(v, list):
                return [_mask(item) for item in v]
            return v

        return _mask(ctx)
