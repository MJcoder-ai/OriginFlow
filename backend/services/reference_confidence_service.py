"""Reference-based confidence estimation service.

This service computes confidence scores for AI actions by retrieving
similar past actions from a vector store and optionally querying an
LLM to infer a nuanced confidence and reasoning.  It implements
hybrid evaluation: if retrieved examples strongly agree on approval or
rejection, the score is derived directly from historical data without
calling the LLM.  It also measures semantic entropy of retrieved
embeddings to determine whether multi-step retrieval is needed, as
proposed by SUGAR【926109218124975†L93-L102】.
"""
from __future__ import annotations

import numpy as np
import re
from typing import Any, Dict, List

from backend.services.embedding_service import EmbeddingService
from backend.services.vector_store import VectorStore

try:
    from openai import OpenAI  # type: ignore
except ImportError:
    OpenAI = None  # type: ignore


class ReferenceConfidenceService:
    """Estimate action confidence using retrieval and optionally LLMs."""

    def __init__(self, vector_store: VectorStore, embedder: EmbeddingService, llm_client: OpenAI | None = None) -> None:
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm_client = llm_client

    async def evaluate_action(self, action: Any, ctx: Dict[str, Any], history: Dict[str, Any]) -> Dict[str, Any]:
        """Compute a confidence score for an AI action."""
        q_vec = await self.embedder.embed_query(action, ctx, history)
        action_type = getattr(action.action, "value", str(action.action))
        retrieved = await self.vector_store.search(q_vec, k=5, filters={"action_type": action_type})

        if not retrieved:
            return {
                "confidence": 0.2,
                "reasoning": "No similar historical examples; defer to human",
                "similar_cases": [],
            }
        similarities = [r["score"] for r in retrieved]
        max_sim = max(similarities)
        if max_sim < 0.5:
            return {
                "confidence": 0.3,
                "reasoning": "Low similarity to historical cases; uncertain",
                "similar_cases": retrieved[:3],
            }
        approvals = [bool(r["payload"].get("approval")) for r in retrieved]
        if all(approvals) or not any(approvals):
            rate = sum(approvals) / len(approvals)
            reasoning = "High consensus in historical data" if rate > 0.5 else "Strong rejection in historical data"
            return {
                "confidence": rate,
                "reasoning": reasoning,
                "similar_cases": retrieved[:3],
            }
        vecs = [q_vec] + [r["vector"] for r in retrieved if r.get("vector")]
        entropy = self._semantic_entropy(vecs)
        if entropy > 0.8:
            more = await self.vector_store.search(q_vec, k=10, filters={})
            retrieved = (retrieved + more)[:5]
        if self.llm_client:
            return await self._llm_evaluation(action, ctx, retrieved[:5])
        rate = sum(approvals) / len(approvals)
        return {
            "confidence": rate,
            "reasoning": "Mixed historical outcomes; average approval used",
            "similar_cases": retrieved[:3],
        }

    def _semantic_entropy(self, vectors: List[List[float]]) -> float:
        """Compute normalized standard deviation of distances to centroid."""
        if not vectors:
            return 0.0
        centroid = np.mean(vectors, axis=0)
        distances = [np.linalg.norm(np.array(v) - centroid) for v in vectors]
        if not distances:
            return 0.0
        mean = float(np.mean(distances))
        std = float(np.std(distances))
        return std / (mean + 1e-6)

    async def _llm_evaluation(self, action: Any, ctx: Dict[str, Any], examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Call LLM to infer confidence and reasoning."""
        examples_text = "\n".join(
            f"{i+1}. Action: {ex['payload'].get('action_type')}\n"
            f"   Component: {ex['payload'].get('component_type')}\n"
            f"   Prompt: \"{ex['payload'].get('user_prompt')}\"\n"
            f"   Result: {'Approved' if ex['payload'].get('approval') else 'Rejected'}"
            for i, ex in enumerate(examples[:3])
        )
        prompt = (
            "You are a decision confidence estimator for an AI design assistant.\n"
            "Past Verified Actions:\n"
            f"{examples_text or 'No similar actions on record.'}\n\n"
            "New Action:\n"
            f"Action: {getattr(action.action, 'value', action.action)}\n"
            f"Prompt: \"{action.payload.get('name') or action.payload.get('type')}\"\n"
            f"Context: {ctx}\n\n"
            "Should we auto-execute this action? Respond with: Confidence score (0.0 to 1.0) and Reasoning."
        )
        response = await self.llm_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200,
        )
        content = response.choices[0].message.content.strip()
        match = re.search(r"([01]?\.\d+)", content)
        confidence = float(match.group(1)) if match else 0.5
        return {
            "confidence": confidence,
            "reasoning": content,
            "similar_cases": examples[:3],
        }
