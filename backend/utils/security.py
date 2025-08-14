"""Security utilities for data sanitisation and PII masking.

This module contains helper functions to detect and mask personally
identifiable information (PII) in user inputs or outputs. Sensitive
patterns include email addresses, phone numbers and credit card
numbers. The masking strategy implemented here preserves the general
structure of the data while obscuring specific characters, allowing
downstream components to recognise the type of information without
exposing private details.

Usage:

```python
from backend.utils.security import mask_pii

data = {"email": "user@example.com", "phone": "+44 1234567890"}
masked = mask_pii(data)
```

The returned dictionary will have the email and phone number masked.
Other values are returned unchanged. This module can be extended
with additional patterns and more sophisticated redaction logic.
"""
from __future__ import annotations

import re
from typing import Any, Dict

EMAIL_REGEX = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
PHONE_REGEX = re.compile(r"(\+?\d[\d\s.-]{7,}\d)")
CREDIT_CARD_REGEX = re.compile(r"(\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b)")


def _mask_email(email: str) -> str:
    """Mask an email address by keeping the first and last character of the
    local part and the domain and replacing the middle with asterisks.
    Example: ``user@example.com`` -> ``u***r@example.com``."""
    match = EMAIL_REGEX.fullmatch(email)
    if not match:
        return email
    local, domain = match.groups()
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def _mask_phone(phone: str) -> str:
    """Mask a phone number by showing only the last four digits.
    All preceding digits are replaced with asterisks, preserving
    separators such as spaces, dashes or dots."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 4:
        return "*" * len(phone)
    masked_digits = "*" * (len(digits) - 4) + digits[-4:]
    result = []
    digit_idx = 0
    for ch in phone:
        if ch.isdigit():
            result.append(masked_digits[digit_idx])
            digit_idx += 1
        else:
            result.append(ch)
    return "".join(result)


def _mask_credit_card(card: str) -> str:
    """Mask a credit card number except for the last four digits.
    Example: ``1234 5678 9012 3456`` -> ``**** **** **** 3456``."""
    digits = re.sub(r"\D", "", card)
    if len(digits) < 4:
        return "*" * len(card)
    masked_digits = "*" * (len(digits) - 4) + digits[-4:]
    result = []
    digit_idx = 0
    for ch in card:
        if ch.isdigit():
            result.append(masked_digits[digit_idx])
            digit_idx += 1
        else:
            result.append(ch)
    return "".join(result)


def mask_pii(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a new dictionary with PII values masked.
    Strings matching email, phone or credit card patterns are redacted.
    Nested dictionaries are processed recursively. Non-string values
    are returned unchanged."""
    masked: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            if CREDIT_CARD_REGEX.fullmatch(value):
                masked[key] = _mask_credit_card(value)
            elif EMAIL_REGEX.fullmatch(value):
                masked[key] = _mask_email(value)
            elif PHONE_REGEX.fullmatch(value):
                masked[key] = _mask_phone(value)
            else:
                masked[key] = value
        elif isinstance(value, dict):
            masked[key] = mask_pii(value)
        else:
            masked[key] = value
    return masked
