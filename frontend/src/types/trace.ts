/**
 * Types for traceability APIs.
 *
 * ``TraceEvent`` corresponds to a single event in a trace series. ``TraceSummary``
 * summarises a trace for listing endpoints.
 */

export interface TraceEvent {
  id: number;
  trace_id: string;
  ts: string;
  actor: string;
  event_type: string;
  payload: Record<string, any>;
  sha256?: string | null;
  prev_sha256?: string | null;
}

export interface TraceSummary {
  trace_id: string;
  first_ts: string;
  last_ts: string;
  count: number;
}
