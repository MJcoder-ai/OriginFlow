# Design Snapshots and Version Control

OriginFlow tracks changes to a design session by capturing **snapshots**,
which store the entire state of the design at a specific moment. Each
snapshot is versioned, enabling undo/redo, branch creation and
historical auditing. This document explains the snapshot schema,
available API endpoints and guidelines for working with versions.

## Snapshot schema

Snapshots are defined in `backend/schemas/analysis.py` via the
`DesignSnapshot` model. A snapshot includes:

- **id**: Optional unique identifier (assigned by the database or API).
- **session_id**: The design session to which this snapshot belongs.
- **timestamp**: UTC timestamp when the snapshot was captured.
- **modified_by**: Identifier of the user or agent who created the snapshot.
- **version**: Monotonically increasing version number within a session.
- **domain**: High‑level domain (e.g. `pv`, `hvac`, `water`).
- **requirements**: Key‑value map of design inputs (e.g. `target_power`).
- **components**: List of nodes (`CanvasComponent` objects) in the single‑line diagram.
- **links**: List of connections (`CanvasLink` objects) in the single‑line diagram.
- **layers**: Optional map of additional layer snapshots, keyed by layer name
  (e.g. `structural`, `wiring`). Each entry is a `LayerSnapshot` with its
  own nodes and links.
- **metadata**: Arbitrary annotations or tags.

This schema ensures that a snapshot can fully reconstruct the design
graph across multiple views and domains.

## Snapshot API

The following endpoints are exposed by `backend/api/routes/snapshots.py`:

| Method | Endpoint | Description |
|-------|----------|-------------|
| `POST` | `/api/v1/snapshots/{session_id}` | Save a new snapshot version for a session. The `version` field is auto‑incremented. |
| `GET`  | `/api/v1/snapshots/{session_id}` | List all snapshots for a session in chronological order. |
| `GET`  | `/api/v1/snapshots/{session_id}/{version}` | Retrieve a single snapshot by version number. Returns 404 if not found. |
| `GET`  | `/api/v1/snapshots/{session_id}/{v1}/diff/{v2}` | Compute a simple diff between two snapshot versions. The response lists added and removed nodes and links. |

Snapshot storage in this implementation is in‑memory and not persistent.
In production, snapshots should be written to a database with indexes on
`session_id` and `version` for efficient retrieval. Authorization
policies should restrict who can create or view snapshots.

## Diffs and version history

The `diff_snapshots` endpoint returns a dictionary with four keys:

- `added_nodes`: IDs of nodes present in the new snapshot but not in the old.
- `removed_nodes`: IDs of nodes present in the old snapshot but not in the new.
- `added_links`: Strings of the form `source_id->target_id` representing
  links added in the new snapshot.
- `removed_links`: Strings representing links removed in the new snapshot.

This basic diff does not detect modifications to node or link
properties; extending it to report changes in attributes or metadata is
left as a future enhancement. Front‑end clients can use diffs to show
visual change indicators or to implement undo/redo operations.

## Branching and tags (future work)

Branching allows users to fork a design into a separate version history
so they can explore alternative solutions. Tagging enables users to
label significant snapshots (e.g. “Preliminary design”, “Approved
structural”) for easier navigation. These features are not yet
implemented in the snapshot service but can be built atop the existing
version storage.

## Best practices

- **Capture snapshots after meaningful edits**: Agents should save a
  snapshot whenever they perform a significant change (e.g. add/remove
  components, wire the system, apply sizing calculations).
- **Limit snapshot frequency**: Avoid excessive snapshot creation for minor
  state updates to prevent version clutter. Decide on a threshold or
  auto‑save frequency based on user interactions.
- **Use metadata**: Populate the `metadata` field with user notes,
  approval states or other context to aid future audits.
- **Persist snapshots**: Integrate the snapshot service with your
  database. Each snapshot’s `id` and `version` can form a composite
  primary key for storage.

With these patterns in place, OriginFlow can provide a robust
versioning experience, enabling traceability, collaboration and
confidence in AI‑driven design changes.
