# backend/tests/test_utils.py
"""Utility tests."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.utils.id import generate_id

def test_generate_id_prefix():
    """Generated IDs contain the prefix."""
    value = generate_id("x")
    assert value.startswith("x_")
