# Intent Firewall (Enterprise Grade)

**Problem:** In multi-agent flows, a wrong `component_type` can slip through when the UI or a planner bypasses the resolver and hits low-level routes (e.g., `/components`) directly.

**Solution:** A server-side *Intent Firewall* that normalizes **every** AI-applied action based on:
1. **Domain Ontology** (multi-domain synonyms)
2. **Explicit mention override** (user says "inverter" → we **must** add an inverter)
3. **Fuzzy matching** (typos like "invertor")

This runs in `/api/v1/ai/apply` and should be the only path the UI uses to apply AI actions. It is domain-agnostic; extend `backend/ai/ontology.py` to support new domains.

## Architecture

```
User Input: "add inverter to the design"
    ↓
Frontend AI Client
    ↓ 
POST /api/v1/ai/apply (Intent Firewall)
    ↓
Domain Ontology Resolution
    ↓
Explicit Intent Override (inverter)
    ↓
Component Creation (generic_inverter)
    ↓
Message: "No inverter in library..."
```

## Key Components

### 1. Domain Ontology (`backend/ai/ontology.py`)

Multi-domain component class resolution:

```python
PV_ONTOLOGY = DomainOntology(
    name="pv",
    synonyms={
        "panel": ["pv module", "module", "solar panel"],
        "inverter": ["string inverter", "microinverter", "micro inverter"],
        "battery": ["battery pack", "energy storage", "ess"],
        # ...
    },
)

HVAC_ONTOLOGY = DomainOntology(
    name="hvac", 
    synonyms={
        "pump": ["circulation pump", "pump"],
        "chiller": ["chiller"],
        # ...
    },
)
```

The resolver matches **whole words and phrases** only, avoiding substring false positives
(e.g., "access point" no longer triggers the battery synonym "ess"). If the text
mentions multiple classes explicitly, the resolver treats it as **ambiguous** and
returns `None`. A fuzzy fallback with a `0.70` cutoff corrects minor typos like
"pupm" → "pump".

### 2. Intent Firewall (`backend/services/ai/action_firewall.py`)

Final normalization logic:

```python
async def normalize_add_component_action(
    *,
    user_text: str,
    snapshot: Optional[DesignSnapshot], 
    payload: Dict,
) -> Dict:
    requested = resolve_canonical_class(user_text or "")
    if requested:
        # User explicitly mentioned a component type - FORCE it
        payload["component_type"] = requested
        payload["type"] = requested
    # else: trust upstream SAAR/agent decision
    return payload
```

### 3. API Endpoint (`backend/api/routes/ai_apply.py`)

The **only** endpoint frontends should use for AI actions:

```python
@router.post("/ai/apply")
async def apply_actions(req: ApplyActionsRequest):
    # Apply Intent Firewall to normalize all actions
    for action in req.actions:
        if action_type == "add_component":
            payload = await normalize_add_component_action(
                user_text=user_text,
                snapshot=snapshot,
                payload=payload
            )
            # Execute normalized action...
```

## **Guarantees**

- ✅ **We never change the class because a library item is missing.** If no real model exists, we fall back to a **placeholder of the same class** (e.g., `generic_inverter`).

- ✅ **If the user explicitly names a class, it overrides priors/heuristics.** "add inverter" will ALWAYS create an inverter, regardless of what any LLM or state prior suggests.

- ✅ **Multi-domain support.** Works for PV, HVAC, networking, and any future domains.

- ✅ **Fuzzy matching.** Handles typos like "invertor" → "inverter".

- ✅ **Defensive logging.** Direct `/components` calls log intent mismatches for monitoring.

## Frontend Integration

**Old (bypasses firewall):**
```typescript
// ❌ Don't do this - bypasses Intent Firewall
await fetch("/api/v1/components/", {
  method: "POST",
  body: JSON.stringify(action.payload)
});
```

**New (uses firewall):**
```typescript
// ✅ Always use this for AI actions
export async function applyAiActions(sessionId: string, actions: any[], userTexts?: string[]) {
  const res = await fetch("/api/v1/ai/apply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      session_id: sessionId, 
      actions, 
      user_texts: userTexts ?? [] 
    }),
  });
  return res.json();
}
```

## Adding New Domains

To support a new domain (e.g., plumbing):

1. **Add domain ontology:**
```python
# backend/ai/ontology.py
PLUMBING_ONTOLOGY = DomainOntology(
    name="plumbing",
    synonyms={
        "pipe": ["pipe", "piping", "pipeline"],
        "valve": ["valve", "shutoff valve", "ball valve"],
        "pump": ["water pump", "sump pump"],  # Note: same as HVAC pump
        # ...
    },
)

DEFAULT_DOMAINS = [PV_ONTOLOGY, HVAC_ONTOLOGY, NETWORK_ONTOLOGY, PLUMBING_ONTOLOGY]
```

2. **Test the new domain:**
```python
def test_plumbing_domain():
    assert resolve_canonical_class("add water pump") == "pump"
    assert resolve_canonical_class("add ball valve") == "valve"
```

The Intent Firewall will automatically handle the new domain with the same guarantees.

## Monitoring

### Intent Mismatch Logging

When AI flows bypass `/ai/apply` and hit `/components` directly, defensive logging captures mismatches:

```
WARNING: Intent mismatch: requested=inverter, created=panel id=comp_123
```

### Firewall Enforcement Logging

```
INFO: Intent Firewall: User explicitly requested 'inverter' from text: 'add inverter to the design' (was: panel)
```

## Testing

Comprehensive test coverage ensures:
- ✅ Explicit mentions override upstream decisions
- ✅ Fuzzy matching handles typos
- ✅ Multi-domain precedence works correctly
- ✅ Ambiguous cases preserve upstream decisions
- ✅ End-to-end flows produce correct results

Run tests:
```bash
pytest backend/tests/test_intent_firewall.py -v
```

## Migration from Old System

1. **Update frontend** to use `/ai/apply` instead of direct component routes
2. **Monitor logs** for intent mismatches to identify remaining bypasses
3. **Gradually deprecate** direct AI calls to `/components` endpoint
4. **Add domain ontologies** as you expand to new component types

The Intent Firewall is backward-compatible and can be deployed incrementally without breaking existing functionality.
