"""In-memory ODL graph service stubs.

This module provides a simple implementation of the OriginFlow ODL
graph service that stores context contracts and design patches in
memory and on disk.  It is intended for demonstration and testing
purposes during the ADPF 2.1 migration; a real implementation would
interact with a persistent graph database and expose network APIs.

Functions defined here include:
    * ``get_contract(session_id)`` – Retrieve a stored context
      contract for a session, or return a new empty contract.
    * ``save_contract(session_id, contract)`` – Persist a context
      contract in memory and to disk.
    * ``add_patch(session_id, patch)`` – Append a result patch to the
      session’s patch list.
    * ``get_patches(session_id)`` – Return the list of patches for a
      session.

Contracts are persisted in the ``storage/contracts`` directory using
the ``ContextContract.save()`` method.  Patches are stored in an
in-memory dictionary keyed by session ID.  This implementation is not
thread-safe and does not handle concurrent modifications; it is
sufficient for single-process scenarios.
"""
from __future__ import annotations

from typing import Any, Dict, List

from backend.models.context_contract import ContextContract

# In-memory stores for contracts and patches.  These are module
# globals; in production they would be replaced by database calls or
# service requests.  Session IDs map to stored objects.
_CONTRACTS: Dict[str, ContextContract] = {}
_PATCHES: Dict[str, List[Dict[str, Any]]] = {}


def get_contract(session_id: str) -> ContextContract:
    """Return the context contract for a session.

    If the contract is cached in memory return it.  Otherwise attempt
    to load it from disk via ``ContextContract.load``.  If no saved
    contract exists a new empty contract is created and cached.

    Args:
        session_id: Unique identifier for the session.

    Returns:
        The ``ContextContract`` associated with the session.
    """
    if session_id in _CONTRACTS:
        return _CONTRACTS[session_id]
    try:
        contract = ContextContract.load(session_id)
    except Exception:
        contract = ContextContract(inputs={})
    _CONTRACTS[session_id] = contract
    return contract


def save_contract(session_id: str, contract: ContextContract) -> None:
    """Persist the context contract for a session.

    The contract is stored in the in-memory cache and written to disk
    via ``ContextContract.save``.  Any errors during disk write are
    silently ignored to avoid crashing the orchestrator.  If the
    provided contract is ``None`` the call does nothing.

    Args:
        session_id: Unique identifier for the session.
        contract: The ``ContextContract`` to persist.
    """
    if contract is None:
        return
    _CONTRACTS[session_id] = contract
    try:
        contract.save(session_id)
    except Exception:
        pass


def add_patch(session_id: str, patch: Dict[str, Any]) -> None:
    """Append a result patch to a session.

    Args:
        session_id: Unique identifier for the session.
        patch: A dictionary representing a result patch.  This can be
            any structure describing modifications to the ODL graph or
            design artefacts.
    """
    if patch is None:
        return
    session_patches = _PATCHES.setdefault(session_id, [])
    session_patches.append(patch)


def get_patches(session_id: str) -> List[Dict[str, Any]]:
    """Return the list of patches recorded for a session.

    Args:
        session_id: Unique identifier for the session.

    Returns:
        A list of patch dictionaries.  If no patches have been
        recorded an empty list is returned.
    """
    return list(_PATCHES.get(session_id, []))

