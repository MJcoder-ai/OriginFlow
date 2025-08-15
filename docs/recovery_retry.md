# Recovery & Retry Utilities (Phase 19)

As OriginFlow designs become more complex, it is critical that blocked tasks
can be resumed once missing context is provided.  The **Recovery & Retry
Utilities** introduced in this phase implement a simple mechanism to
capture blocked tasks and automatically retry them after relevant
information becomes available.

## RetryManager

The `RetryManager` (defined in `backend/utils/retry_manager.py`) is a
central component responsible for tracking blocked tasks.  When an
agent returns an ADPF envelope with `status='blocked'`, the task is
registered with the retry manager along with its agent name, task
identifier and context.  A per‑session queue stores blocked tasks
until they can be retried.

To attempt resolution, call `retry_manager.resolve_blocked_tasks(session_id)`.
This iterates through the queued tasks for the session, invoking each
agent’s `safe_execute` method.  Tasks that succeed (i.e. return a
status other than `blocked`) are removed from the queue.  Remaining
tasks stay in the queue for future attempts.

## AgentBase & safe_execute

All agents in this minimal codebase now inherit from `AgentBase`
(defined in `backend/agents/base.py`).  The base class provides a
`safe_execute` wrapper around the agent’s `execute` method:

- **Error Handling:** Any uncaught exceptions in `execute` are
  captured and returned as a fallback ADPF envelope with a
  descriptive error message and `status='blocked'`.
- **Blocked Task Registration:** If an agent returns a result with
  `status='blocked'`, `safe_execute` automatically registers the
  task with the global retry manager, preserving the original
  context (e.g. missing fields or reason strings).

Developers should call `safe_execute` instead of `execute` when
invoking agents in a production environment to ensure blocked tasks
are properly tracked and retried.

## Usage Example

Suppose a design agent cannot proceed because a datasheet is missing.
It returns an envelope:

```python
{
    "thought": "Missing datasheet for the inverter.",
    "output": {
        "card": { "title": "Inverter Design", "body": "Please upload the inverter datasheet." },
        "patch": None,
    },
    "status": "blocked",
}
```

If invoked via `safe_execute`, the agent registers this task with the
retry manager.  After the user uploads the datasheet, calling
`retry_manager.resolve_blocked_tasks(session_id)` will re‑execute the
task.  If the datasheet is available, the agent completes and the
task is removed from the blocked queue.

## Future Work

This basic retry mechanism serves as a placeholder for more robust
systems.  A production implementation may integrate with a workflow
engine (such as Temporal.io) to persist blocked tasks, schedule
retries, and provide user notifications when a task resumes or still
requires attention.

