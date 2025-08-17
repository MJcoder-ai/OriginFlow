# Graph Version Synchronisation

OriginFlow uses a *graph version* counter to ensure that clients do not
unknowingly mutate an outdated design. The backend increments this
counter whenever the design graph changes. When the frontend calls
`POST /odl/sessions/{session_id}/act`, it must include the version
number it believes to be current; if the server's version is newer,
the request is rejected with a **409 Conflict**. Previously, the
frontend initialised the version to `0` and only updated it after the
first `act` call succeeded, causing an avoidable 409 on the first
attempt.

## How it works now

The application now synchronises the graph version immediately after
fetching a new plan. The Zustand store exposes a `syncGraphVersion`
helper which calls
`GET /odl/sessions/{session_id}/text` to retrieve the latest ODL
representation. The returned object contains a `version` field, which
is stored in `graphVersion`. After every call to
`getPlanForSession`, the frontend invokes this helper to ensure that
subsequent calls to `act` include the correct version and do not
trigger an initial 409.

## Why this matters

Synchronising the version early improves user experience by avoiding
unnecessary "version conflict" messages and eliminates one round-trip
to the server. It also reduces confusion when rapidly iterating on a
design, since the UI always knows which version of the graph it is
operating on.

If you add new flows that fetch a plan or otherwise mutate the design,
remember to call `syncGraphVersion(sessionId)` afterwards.
