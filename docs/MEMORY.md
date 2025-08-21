# Memory (Scratchpad)

The memory layer stores **small structured state** that helps the orchestrator:
requirements, last decisions, and hints to minimize LLM context. It is **not**
a conversational transcript. See `backend/memory/scratchpad.py`.

### Suggested fields
```json
{
  "requirements": {"target_power": 5000, "roof_area": 32.0},
  "last_task": "replace_placeholders",
  "last_decision": "review_required"
}
```
