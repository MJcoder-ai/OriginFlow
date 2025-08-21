import { act } from './api';
import { API_BASE_URL } from '../config';

async function getHeadVersion(sessionId: string): Promise<number> {
  const res = await fetch(`${API_BASE_URL}/odl/${encodeURIComponent(sessionId)}/head`);
  if (!res.ok) throw new Error(`Failed to get head: ${res.status}`);
  const j = await res.json();
  return Number(j?.version ?? 0);
}

/**
 * Execute a plan by calling POST /api/v1/ai/act for each task with If-Match.
 * Assumes each task has the args expected by the orchestrator.
 */
export async function runPlan(
  sessionId: string,
  plan: { tasks: Array<{ id: string; args?: any }> },
): Promise<void> {
  let version = await getHeadVersion(sessionId);
  for (const t of plan.tasks) {
    const args = t.args ?? {};
    await act(sessionId, t.id, args, version);
    version = await getHeadVersion(sessionId);
  }
}

