# State-Aware Action Resolver (SAAR)

## Summary
SAAR makes component actions **context-aware and deterministic** without brittle if/else rules.  
Given a user command + current design snapshot, it chooses the best `component_class`
(`panel`, `inverter`, …) using:

- **Semantic similarity** to *class prototypes* (embeddings)
- **State-conditioned priors** (requirements vs inventory)
- A **closed JSON schema** (`ActionRequest`) for tool-calling/validation

This removes the legacy “default to inverter” behavior and prevents panel→inverter misclassifications.

## What changes
- New schema: `backend/schemas/actions.py` with `ActionRequest`.
- New ontology & prototypes: `backend/ai/ontology.py`.
- New resolver: `backend/services/ai/state_action_resolver.py`.
- Component agent now uses the resolver before materializing `add_component` actions.

## How it works
1. **Design context**: a lightweight summary provides counts and requirement estimates.
2. **Prototype embeddings**: we embed class descriptions (synonyms + anchors).
3. **Score & pick**: similarity (w=0.7) + priors (w=0.3) → softmax → `component_class`.
4. **Emit**: `ActionRequest(action="add_component", component_class=...)` with confidence+rationale.
5. **Downstream** (unchanged): real vs placeholder selection continues using existing library logic.

## Telemetry
For each decision we attach:
```json
{ "_resolver": { "confidence": 0.83, "rationale": "Similarity=0.92, Priors=0.10" } }
```
Log these for continuous improvement.

## Extending
- Add new classes by appending synonyms/anchors in `ontology.py`.
- Tune weights in the resolver or replace with a trained classifier.
- To incorporate LLM ranking, feed the resolver’s features to the LLM and
  require it to output `ActionRequest`; keep the deterministic fallback.

## Guarantees
- **Closed enum** prevents invalid classes.
- **No silent defaults** (never defaults to inverter).
- **Fast**: prototype embeddings cached; single encode per user turn.
