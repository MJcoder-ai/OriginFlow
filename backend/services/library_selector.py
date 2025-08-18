from __future__ import annotations
"""
Real-vs-Placeholder selector for add_component operations.

The selector prefers real library models when they satisfy high level
requirements and gracefully falls back to placeholders when no suitable
candidate is found.  The implementation is intentionally lightweight so it
can be used from both synchronous and asynchronous contexts without pulling
in heavy dependencies.
"""

from typing import Optional, Dict, Any, List, Tuple

from backend.schemas.actions import ComponentClass
from backend.schemas.analysis import DesignSnapshot

# Heuristic attribute names used when scoring components.  These keys map to
# values in the component library's attribute dictionaries.  They are
# intentionally conservative so the selector still works if the underlying
# schema changes slightly.
PANEL_PMAX_FIELD = "pmax_w"
INVERTER_ACKW_FIELD = "ac_power_kw"
INVERTER_MPPTS_FIELD = "mppt_count"


class LibrarySelector:
    """Select an appropriate library model for a component class.

    The selector is designed to be deterministic.  It queries a lightweight
    repository interface if available.  When the repository cannot be
    imported (for example in unit tests) the selector simply returns ``None``
    to indicate that a generic placeholder should be used instead.
    """

    def __init__(self) -> None:  # pragma: no cover - import guarded
        try:
            from backend.repositories.library import LibraryRepo  # type: ignore

            self._repo = LibraryRepo()
        except Exception:  # pragma: no cover - repository optional
            self._repo = None

    async def _list_models(
        self, component_class: ComponentClass
    ) -> List[Dict[str, Any]]:
        """Return a list of available models for ``component_class``.

        Each entry is a mapping with at minimum ``id`` and ``attrs`` keys.  If
        the repository is unavailable an empty list is returned.
        """

        if self._repo is None:
            return []

        return await self._repo.list_models_by_class(component_class)  # type: ignore

    # ------------------------------------------------------------------
    # Scoring helpers
    def _requirements(self, snapshot: Optional[DesignSnapshot]) -> Dict[str, Any]:
        meta = getattr(snapshot, "metadata", {}) or {}
        return meta.get("requirements") or {}

    def _power_gap_w(self, snapshot: Optional[DesignSnapshot]) -> Optional[float]:
        """Estimate the remaining DC power gap from requirements."""

        if not snapshot:
            return None
        req = self._requirements(snapshot)
        target_kw = req.get("target_power") or req.get("target_power_kw")
        if not target_kw:
            return None
        total_panel_w = 0.0
        for comp in snapshot.components:
            attrs = getattr(comp, "attributes", None) or {}
            pmax = attrs.get(PANEL_PMAX_FIELD)
            if pmax:
                total_panel_w += float(pmax)
        gap_w = float(target_kw) * 1000.0 - total_panel_w
        return max(gap_w, 0.0)

    def _score_panel(self, model: Dict[str, Any], gap_w: Optional[float]) -> float:
        attrs = model.get("attrs", {})
        pmax = attrs.get(PANEL_PMAX_FIELD)
        if pmax is None:
            return 0.0
        pmax = float(pmax)
        base = 1.0 if 350 <= pmax <= 550 else 0.6
        if gap_w is None or gap_w <= 0:
            return base
        return base * (1.0 / (1.0 + abs(gap_w - pmax) / max(gap_w, 1.0)))

    def _score_inverter(
        self, model: Dict[str, Any], snapshot: Optional[DesignSnapshot]
    ) -> float:
        attrs = model.get("attrs", {})
        ackw = attrs.get(INVERTER_ACKW_FIELD)
        mppts = attrs.get(INVERTER_MPPTS_FIELD, 1)
        if ackw is None:
            return 0.0
        ackw = float(ackw)
        total_dc_kw = 0.0
        if snapshot:
            for comp in snapshot.components:
                if "panel" in comp.type:
                    attrs = getattr(comp, "attributes", None) or {}
                    pmax = attrs.get(PANEL_PMAX_FIELD)
                    if pmax:
                        total_dc_kw += float(pmax) / 1000.0
        ratio = total_dc_kw / max(ackw, 0.1)
        ratio_score = 1.0 if 1.0 <= ratio <= 1.3 else max(0.0, 1.3 - abs(1.15 - ratio))
        mppt_score = 1.0 if mppts and mppts >= 2 else 0.7
        return 0.5 * ratio_score + 0.5 * mppt_score

    # ------------------------------------------------------------------
    async def choose_model_or_placeholder(
        self,
        component_class: ComponentClass,
        snapshot: Optional[DesignSnapshot],
    ) -> Tuple[Optional[str], str]:
        """Return ``(model_id, reason)`` for the chosen component.

        ``model_id`` is ``None`` when no suitable library model exists.  In that
        case the caller should use ``generic_<class>`` placeholder components.
        """

        models = await self._list_models(component_class)
        if not models:
            return None, "no_real_models_available"

        if component_class == "panel":
            gap = self._power_gap_w(snapshot)
            scored = [(m, self._score_panel(m, gap)) for m in models]
        elif component_class == "inverter":
            scored = [(m, self._score_inverter(m, snapshot)) for m in models]
        else:
            scored = [(m, 1.0 if m.get("attrs") else 0.5) for m in models]

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[0][0] if scored else None
        if not top or scored[0][1] <= 0.0:
            return None, "no_suitable_model_scored"
        return top.get("id"), "selected_best_fit"


__all__ = ["LibrarySelector"]

