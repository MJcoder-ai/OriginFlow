from __future__ import annotations
from typing import Dict, List, Optional
import math

import numpy as np

from backend.schemas.actions import ActionRequest, ComponentClass
from backend.schemas.analysis import DesignSnapshot
from backend.ai.ontology import iter_prototype_texts
from backend.services.design_context import priors_for_next_step

try:  # sentence-transformer is optional in some environments
    from backend.services.embedding_service import get_sentence_embedder  # type: ignore
except Exception:  # pragma: no cover - embedder init failure
    get_sentence_embedder = None


def _softmax(xs: List[float]) -> List[float]:
    m = max(xs) if xs else 0.0
    exps = [math.exp(x - m) for x in xs]
    s = sum(exps) or 1.0
    return [e / s for e in exps]


class StateAwareActionResolver:
    """Resolve user intent into structured ActionRequest."""

    def __init__(self) -> None:
        if get_sentence_embedder is None:
            raise RuntimeError(
                "EmbeddingService not available. Ensure get_sentence_embedder() is defined."
            )
        self._embedder = get_sentence_embedder()
        self._proto_texts = iter_prototype_texts()
        self._proto_vecs = {
            cls: self._embedder.encode(txt) for cls, txt in self._proto_texts.items()
        }

    def class_similarity(self, user_text: str) -> Dict[str, float]:
        q = self._embedder.encode(user_text or "")
        sims: Dict[str, float] = {}
        for cls, v in self._proto_vecs.items():
            sims[cls] = float(np.dot(q, v))
        if sims:
            lo, hi = min(sims.values()), max(sims.values())
            rng = (hi - lo) or 1e-6
            for k in sims:
                sims[k] = (sims[k] - lo) / rng
        return sims

    def resolve_add_component(
        self,
        user_text: str,
        snapshot: Optional[DesignSnapshot],
        default_layer: str = "single_line",
    ) -> ActionRequest:
        # Check for explicit mention override first
        explicit_class = self._explicit_class_from_text(user_text)
        if explicit_class:
            return ActionRequest(
                action="add_component",
                component_class=explicit_class,  # type: ignore[arg-type]
                quantity=1,
                target_layer=default_layer,
                confidence=0.99,  # High confidence for explicit mentions
                rationale=f"Explicit mention of '{explicit_class}' in user text",
            )
        
        # Fall back to similarity + priors approach
        sims = self.class_similarity(user_text)
        priors = priors_for_next_step(snapshot)
        classes: List[str] = sorted(sims.keys())
        raw_scores: List[float] = []
        WEIGHT_SIM, WEIGHT_PRI = 0.7, 0.3
        for cls in classes:
            prior = priors.get(f"add_component.{cls}", 0.0)
            raw_scores.append(WEIGHT_SIM * sims.get(cls, 0.0) + WEIGHT_PRI * prior)
        probs = _softmax(raw_scores) if raw_scores else []
        if not classes:
            return ActionRequest(action="analyze", rationale="no_classes_available", confidence=0.0)
        idx = int(max(range(len(probs)), key=lambda i: probs[i]))
        best_cls = classes[idx]
        confidence = float(probs[idx])
        return ActionRequest(
            action="add_component",
            component_class=best_cls,  # type: ignore[arg-type]
            quantity=1,
            target_layer=default_layer,
            confidence=confidence,
            rationale=f"Similarity={sims.get(best_cls,0):.2f}, Priors={priors.get('add_component.'+best_cls,0):.2f}",
        )

    def _explicit_class_from_text(self, text: str) -> Optional[str]:
        """Detect explicitly mentioned component class from user text."""
        try:
            from backend.ai.ontology import ONTOLOGY
            
            text_lower = text.lower()
            hits = []
            
            for cls, synonyms in ONTOLOGY.classes.items():
                # Check class name and all synonyms
                all_terms = [cls.lower()] + [syn.lower() for syn in synonyms]
                if any(term in text_lower for term in all_terms):
                    hits.append(cls)
            
            # Return class only if exactly one is mentioned (unambiguous)
            unique_hits = list(set(hits))
            return unique_hits[0] if len(unique_hits) == 1 else None
            
        except Exception:
            return None
