# AI Feedback Logging

OriginFlow records decisions about AI-suggested actions so future
confidence models and audits have a reliable data trail. The
``LearningAgent`` reads these logs to compute empirical approval rates
and adjust confidence scores for new AI actions.

## Endpoints

### v1: `POST /api/v1/ai/log-feedback`

The original endpoint persists raw feedback to the `ai_action_log` table
for auditing and empirical confidence estimation.

#### Payload

- `session_id` (string, optional): Correlates feedback to a user session.
- `prompt_text` (string, optional): Original natural-language request.
- `proposed_action` (object): The action suggested by the AI.
- `user_decision` (string): `approved`, `rejected`, or `auto`.

### v2: `POST /api/v1/ai/log-feedback-v2`

The enriched endpoint stores both the raw log and an anonymized,
embedded representation in the `ai_action_vectors` table and vector
store.  It supports all fields from v1 and adds:

- `user_prompt` (string, required): Original natural-language command.
- `component_type` (string, optional): Type of component being added.
- `design_context` (object, optional): Current design context as JSON.
- `session_history` (object, optional): Recent actions and context history.
- `confidence_shown` (number, optional): Confidence score displayed to the user.
- `confirmed_by` (string, optional): `human` or `auto` confirmation.

Before embedding, prompts and contexts are passed through a simple
anonymizer that redacts basic PII like emails and phone numbers.  The
resulting text is embedded using a SentenceTransformer model (or OpenAI
fallback) and upserted into the configured vector store (Qdrant by
default).

Both endpoints return `200 OK` on success and are backward compatible.

## Frontend Integration

The checklist UI logs an entry whenever a user approves or rejects an AI
action before the operation is applied to the canvas.  New fields for
v2 should be provided by the caller to enable anonymization and
embedding.

## Creating New Embeddings

Developers can experiment with alternative embedding models by setting
the `EMBED_MODEL` environment variable or by overriding
`EmbeddingService`. The `log-feedback-v2` endpoint and the
`LearningAgent` both support dependency injection, allowing tests or
custom deployments to supply mock vector stores or embedding services.
When the vector store is unavailable, the `LearningAgent` falls back to empirical approval ratios from the
`ai_action_log` table, ensuring confidence scores are still provided even
without retrieval.
