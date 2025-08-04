"""Symmetric encryption for embedding vectors.

This module wraps the `cryptography` library's Fernet implementation
to encrypt and decrypt embeddings before storing them in the database.
Fernet uses AES‑128 in CBC mode with HMAC authentication.  If you
prefer AES‑256, consider using PyCryptodome or another library.
"""
from __future__ import annotations

import json
from typing import List

try:
    from cryptography.fernet import Fernet  # type: ignore
except ImportError:
    Fernet = None  # type: ignore


def generate_key() -> bytes:
    """Generate a new encryption key."""
    if Fernet is None:
        raise RuntimeError("cryptography package is not installed")
    return Fernet.generate_key()


def encrypt_vector(vec: List[float], key: bytes) -> bytes:
    """Encrypt a vector of floats using Fernet."""
    if Fernet is None:
        raise RuntimeError("cryptography package is not installed")
    fernet = Fernet(key)
    data = json.dumps(vec).encode("utf-8")
    return fernet.encrypt(data)


def decrypt_vector(token: bytes, key: bytes) -> List[float]:
    """Decrypt an embedding vector."""
    if Fernet is None:
        raise RuntimeError("cryptography package is not installed")
    fernet = Fernet(key)
    decrypted = fernet.decrypt(token)
    return json.loads(decrypted.decode("utf-8"))
