/**
 * Type definitions for memory entries returned by the API.
 *
 * Mirrors the server side ``Memory`` Pydantic schema. Optional
 * properties such as ``project_id`` and ``tags`` are represented
 * accordingly. ``created_at`` is an ISO timestamp string.
 */
export interface Memory {
  id: number;
  tenant_id: string;
  project_id?: string | null;
  kind: string;
  created_at: string;
  tags?: Record<string, any> | null;
  trace_id?: string | null;
  sha256?: string | null;
  prev_sha256?: string | null;
}
