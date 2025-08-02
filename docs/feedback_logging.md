# AI Feedback Logging

OriginFlow records decisions about AI-suggested actions so future
confidence models and audits have a reliable data trail. The
``LearningAgent`` reads these logs to compute empirical approval rates
and adjust confidence scores for new AI actions.

## Endpoint

`POST /api/v1/ai/log-feedback`

### Payload

- `session_id` (string, optional): Correlates feedback to a user session.
- `prompt_text` (string, optional): Original natural-language request.
- `proposed_action` (object): The action suggested by the AI.
- `user_decision` (string): `approved`, `rejected`, or `auto`.

 A successful request returns `200 OK`.

## Frontend Integration

The checklist UI logs an entry whenever a user approves or rejects an AI
action before the operation is applied to the canvas.
