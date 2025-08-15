# Contract‑First Schema Enforcement (Phase 20)

As OriginFlow’s agent ecosystem grows, it becomes increasingly important to
enforce a consistent output structure across all agents.  Phase 20
introduces **Contract‑First Schema Enforcement**, ensuring that every
agent response conforms to a declared schema before it is consumed by
downstream components.

## ADPF Envelope Schema

All agents return their outputs wrapped in a standard JSON object known as
an **ADPF envelope**.  The envelope contains at minimum these keys:

- **thought** – a string summarising the agent’s reasoning.
- **output** – an object containing a **card** and optionally a **patch**.
  The **card** holds user-facing information such as titles, bodies,
  questions, recommended actions or other agent-specific fields.  The
  **patch** represents changes to the design graph or may be `null`.
- **status** – one of `complete`, `pending` or `blocked`.
- **warnings** (optional) – a list of strings warning about any issues
  encountered during execution.

To formalise this contract, the module `backend/utils/schema_enforcer.py`
defines a JSON Schema (`ADPF_ENVELOPE_SCHEMA`) and provides a function
`validate_envelope` that checks a response against this schema using
the `jsonschema` library.

## Validation in `safe_execute`

The `AgentBase.safe_execute` wrapper now validates every envelope returned
from an agent.  If the envelope fails validation, `safe_execute`
produces a new blocked response informing the user that the agent
returned an invalid structure.  This prevents malformed outputs from
propagating through the system and makes debugging easier.

Agents may extend the envelope with additional fields (e.g.
`selected_card` in the consensus agent) because the schema permits
additional properties by default.  However, they must always include
the required keys (`thought`, `output`, `status`) and a `card`
within `output`.

## Agent‑Specific Contracts

While the ADPF envelope schema covers the common structure, agents are
encouraged to define their own detailed schemas for their `card` and
`patch` fields.  For example, a structural design agent might require
that its card include `warnings` and `specs` keys, while a network
agent could require `device_type` and `instrumented_components`.

Future versions of OriginFlow may include per‑agent schema definitions
and centralised validation, allowing the orchestrator to enforce
contract compliance across all layers.

## Getting Started

Developers adding new agents should:

1. Ensure the agent’s `execute` method returns a dictionary with the
   required keys and a valid envelope structure.
2. Use `safe_execute` to invoke the agent so that schema validation
   occurs automatically.
3. Optionally, define and document a JSON Schema for the agent’s card
   and patch formats to aid in long‑term maintenance and testing.

By adopting contract‑first schema enforcement, OriginFlow reduces
unexpected runtime errors and improves reliability as more domains and
agents are added.
