/**
 * Collection of API helpers used by the frontend (OriginFlow API).
 *
 * Canonical OriginFlow backend endpoints:
 *   - POST /api/v1/odl/sessions?session_id={sid}
 *   - GET  /api/v1/odl/sessions/{sid}/plan?command=...
 *   - POST /api/v1/ai/act
 *   - GET  /api/v1/odl/{sid}/view?layer=...
 *   - GET  /api/v1/odl/sessions/{sid}/text
 *
 * This module gracefully degrades when legacy endpoints are missing.
 */
import { CanvasComponent, Link, PlanTask } from '../appStore';
import { AiAction } from '../types/ai';
import { DesignSnapshot } from '../types/analysis';
import { API_BASE_URL } from '../config';

export type AiPlan = {
  tasks: { id: string; title: string; description?: string; status: 'pending' | 'in_progress' | 'complete' | 'blocked' }[];
  metadata?: Record<string, any>;
};

const genId = () =>
  (globalThis as any)?.crypto?.randomUUID?.() ||
  `req_${Math.random().toString(36).slice(2)}_${Date.now()}`;

export type ComponentCreateDTO = Omit<CanvasComponent, 'id' | 'ports'>;
/** Payload for creating a link via the backend API. */
export type LinkCreateDTO = Omit<Link, 'id'>;

export interface QuickAction {
  id: string;
  label: string;
  command: string;
}

export interface PlanResponse {
  tasks: PlanTask[];
  quick_actions?: QuickAction[];
  metadata?: Record<string, any>;
}

export interface GraphPatch {
  add_nodes?: Array<{
    id: string;
    type: string;
    data?: Record<string, any>;
    layer?: string;
  }>;
  add_edges?: Array<{
    source: string;
    target: string;
    data?: Record<string, any>;
  }>;
  remove_nodes?: string[];
  remove_edges?: Array<{
    source: string;
    target: string;
  }>;
}

export interface TaskExecutionResponse {
  patch?: GraphPatch;
  card?: {
    title: string;
    body: string;
    confidence?: number;
    specs?: Array<{
      label: string;
      value: string;
      unit?: string;
      confidence?: number;
    }>;
    actions?: Array<{
      label: string;
      command: string;
      variant?: string;
      enabled?: boolean;
      icon?: string;
    }>;
    warnings?: string[];
    recommendations?: string[];
  };
  status: 'pending' | 'in_progress' | 'complete' | 'blocked';
  version?: number;
  updated_tasks?: any[];
  next_recommended_task?: string | null;
  execution_time_ms?: number;
}

export async function act(
  sessionId: string,
  taskId: string,
  args?: any,
  graphVersion?: number,
): Promise<TaskExecutionResponse> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (typeof graphVersion === 'number') headers['If-Match'] = String(graphVersion);
  const res = await fetch(`${API_BASE_URL}/ai/act`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      session_id: sessionId,
      task: taskId,
      request_id: genId(),
      args,
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    const error: any = new Error(`Act endpoint error ${res.status}: ${text.slice(0, 120)}`);
    error.status = res.status;
    error.detail = text;
    throw error;
  }
  return res.json();
}

// --- Minimal client-side fallback planner ------------------------------------
function fallbackPlanFromPrompt(command: string, layer: string = 'single-line'): AiPlan {
  const lower = (command || '').toLowerCase();
  const kwMatch = /(\d+(?:\.\d+)?)\s*kw\b/.exec(lower);
  const targetKW = kwMatch ? parseFloat(kwMatch[1]) : 5;
  const wattsMatch = /(panel|module)[^0-9]*?(\d{3,4})\s*w\b/.exec(lower);
  const panelW = wattsMatch ? Math.min(700, Math.max(250, parseInt(wattsMatch[2], 10))) : 400;
  const count = Math.max(1, Math.ceil((targetKW * 1000) / panelW));
  return {
    tasks: [
      {
        id: 'make_placeholders',
        title: 'Create inverter',
        description: `Add one inverter on the ${layer} layer`,
        status: 'pending',
        args: { component_type: 'inverter', count: 1, layer },
      } as any,
      {
        id: 'make_placeholders',
        title: `Create ${count} panels`,
        description: `Add ${count} x ~${panelW}W panels on the ${layer} layer`,
        status: 'pending',
        args: { component_type: 'panel', count, layer },
      } as any,
      {
        id: 'generate_wiring',
        title: 'Generate wiring',
        description: `Auto-connect inverter and panels on ${layer} layer`,
        status: 'pending',
        args: { layer },
      } as any,
    ],
    metadata: { fallback: true, targetKW, panelW, count, layer },
  };
}

/** @deprecated OriginFlow removed this route. Use `getPlanForSession` + `act` instead. */
let _warnedAnalyzeDesign = false;

export const api = {
  async getComponents(): Promise<CanvasComponent[]> {
    const response = await fetch(`${API_BASE_URL}/components/`);
    if (!response.ok) throw new Error('Failed to fetch components');
    return response.json();
  },

  async getLinks(): Promise<Link[]> {
    const response = await fetch(`${API_BASE_URL}/links/`);
    if (!response.ok) throw new Error('Failed to fetch links');
    return response.json();
  },

  async createComponent(componentData: ComponentCreateDTO): Promise<CanvasComponent> {
    const response = await fetch(`${API_BASE_URL}/components/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(componentData),
    });
    if (!response.ok) throw new Error('Failed to create component');
    return response.json();
  },

  async createLink(linkData: LinkCreateDTO): Promise<Link> {
    const response = await fetch(`${API_BASE_URL}/links/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(linkData),
    });
    if (!response.ok) throw new Error('Failed to create link');
    return response.json();
  },

  async updateComponent(
    id: string,
    updateData: Partial<ComponentCreateDTO>
  ): Promise<CanvasComponent> {
    const response = await fetch(`${API_BASE_URL}/components/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updateData),
    });
    if (!response.ok) throw new Error('Failed to update component');
    return response.json();
  },

  async deleteComponent(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/components/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete component');
  },

  /** Get a high-level plan (optionally for a specific ODL session). */
  async getPlan(
    command: string,
    options?: { sessionId?: string }
  ): Promise<PlanResponse> {
    let res: Response;
    if (options?.sessionId) {
      const url = `${API_BASE_URL}/odl/sessions/${encodeURIComponent(
        options.sessionId
      )}/plan?command=${encodeURIComponent(command)}`;
      res = await fetch(url);
    } else {
      res = await fetch(`${API_BASE_URL}/ai/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      });
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Plan endpoint error ${res.status}: ${text.slice(0, 120)}`);
    }
    return res.json();
  },

  async analyzeDesign(
    _snapshot: DesignSnapshot,
    _command: string
  ): Promise<AiAction[]> {
    if (!_warnedAnalyzeDesign && typeof console !== 'undefined') {
      _warnedAnalyzeDesign = true;
      console.warn(
        '[deprecated] analyzeDesign(): removed. Call getPlanForSession() then act().'
      );
    }
    return [];
  },

  act,

  /**
   * Create or reset an ODL design session.  Must be called before
   * using `/odl/sessions/{session_id}/plan` or `/odl/sessions/{session_id}/act`.
   */
  async createOdlSession(sessionId?: string): Promise<{ session_id: string }> {
    const url = sessionId
      ? `${API_BASE_URL}/odl/sessions?session_id=${encodeURIComponent(sessionId)}`
      : `${API_BASE_URL}/odl/sessions`;
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Create session error ${res.status}: ${text.slice(0, 200)}`);
    }
    return res.json();
  },

  /**
   * Get a plan tailored to a specific ODL session.  Uses
   * `/odl/sessions/{session_id}/plan` to return tasks and quick actions
   * appropriate for the current graph. Falls back to a tiny client-side
   * planner if the server route is unavailable.
   */
  async getPlanForSession(
    sessionId: string,
    command: string,
    layer: string = 'single-line',
  ): Promise<{ tasks: any[]; quick_actions?: any[]; metadata?: Record<string, any> }> {
    try {
      const params = new URLSearchParams({ command, layer });
      const res = await fetch(
        `${API_BASE_URL}/odl/sessions/${encodeURIComponent(sessionId)}/plan?${params.toString()}`
      );
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          return { tasks: data } as any;
        }
        return data;
      }
      if (res.status === 404 || res.status === 410) {
        return fallbackPlanFromPrompt(command, layer) as any;
      }
      const text = await res.text();
      throw new Error(`Plan session error ${res.status}: ${text.slice(0, 200)}`);
    } catch {
      return fallbackPlanFromPrompt(command, layer) as any;
    }
  },

  /** POST a natural-language command and receive deterministic actions. */
  async sendCommandToAI(command: string): Promise<AiAction[]> {
    const res = await fetch(`${API_BASE_URL}/ai/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command }),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`AI endpoint error ${res.status}: ${text.slice(0, 120)}`);
    }
    return res.json();
  },

  async postRequirements(sessionId: string, requirements: Record<string, any>): Promise<void> {
    const res = await fetch(
      `${API_BASE_URL}/odl/sessions/${encodeURIComponent(sessionId)}/requirements`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements }),
      }
    );
    if (!res.ok) throw new Error(`Requirements update failed: ${res.status}`);
  },

  async ingestComponent(payload: { category: string; part_number: string; attributes: Record<string, any> }) {
    const res = await fetch(`${API_BASE_URL}/components/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Component ingest failed: ${res.status}`);
    return res.json();
  },

  async revertToVersion(sessionId: string, targetVersion: number): Promise<{ detail: string; version: number }> {
    const res = await fetch(
      `${API_BASE_URL}/odl/sessions/${encodeURIComponent(sessionId)}/revert`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_version: targetVersion }),
      }
    );
    if (!res.ok) throw new Error(`Revert failed: ${res.status}`);
    const data = await res.json();
    // Normalize to existing consumer shape
    return { detail: data.message, version: data.current_version };
  },

  async listAgentTasks(): Promise<{ agents: any; task_types: string[] }> {
    const res = await fetch(`${API_BASE_URL}/odl/agents`);
    if (!res.ok) throw new Error(`List tasks failed: ${res.status}`);
    return res.json();
  },

  // ---- Agents Catalog (persistence/RBAC) ----
  async listTenantAgentState(tenantId?: string) {
    const url = tenantId
      ? `/api/v1/odl/agents/state?tenant_id=${encodeURIComponent(tenantId)}`
      : `/api/v1/odl/agents/state`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to list tenant agent state');
    return res.json();
  },

  async createAgentDraft(spec: any) {
    const res = await fetch(`/api/v1/odl/agents/drafts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ spec }),
    });
    if (!res.ok) throw new Error('Failed to create draft');
    return res.json();
  },

  async publishAgent(agentName: string, version?: number, notes?: string) {
    const res = await fetch(`/api/v1/odl/agents/${encodeURIComponent(agentName)}/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ version, notes }),
    });
    if (!res.ok) throw new Error('Failed to publish agent');
    return res.json();
  },

  async updateTenantAgentState(
    agentName: string,
    patch: { enabled?: boolean; pinned_version?: number; config_override?: any },
    tenantId?: string
  ) {
    const url = `/api/v1/odl/agents/${encodeURIComponent(agentName)}/state${tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : ''}`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    });
    if (!res.ok) throw new Error('Failed to update tenant agent state');
    return res.json();
  },

  async assistSynthesizeSpec(idea: string, target_domain?: string, target_actions?: string[]) {
    const res = await fetch(`/api/v1/odl/agents/assist/synthesize-spec`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ idea, target_domain, target_actions }),
    });
    if (!res.ok) throw new Error('Failed to synthesize spec');
    return res.json();
  },

  async assistRefineSpec(current_spec: any, critique: string) {
    const res = await fetch(`/api/v1/odl/agents/assist/refine-spec`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_spec, critique }),
    });
    if (!res.ok) throw new Error('Failed to refine spec');
    return res.json();
  },

  // ---- Approvals ----
  async listApprovals(params: { status?: string; session_id?: string; project_id?: string; limit?: number; offset?: number } = {}) {
    const qs = new URLSearchParams();
    if (params.status) qs.set('status', params.status);
    if (params.session_id) qs.set('session_id', params.session_id);
    if (params.project_id) qs.set('project_id', params.project_id);
    if (params.limit) qs.set('limit', String(params.limit));
    if (params.offset) qs.set('offset', String(params.offset));
    const res = await fetch(`/api/v1/approvals/?${qs.toString()}`);
    if (!res.ok) throw new Error('Failed to list approvals');
    return res.json();
  },
  async approveApproval(id: number, note?: string, approve_and_apply: boolean = false) {
    const res = await fetch(`/api/v1/approvals/${id}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note, approve_and_apply }),
    });
    if (!res.ok) throw new Error('Failed to approve');
    return res.json();
  },
  async rejectApproval(id: number, note?: string) {
    const res = await fetch(`/api/v1/approvals/${id}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note }),
    });
    if (!res.ok) throw new Error('Failed to reject');
    return res.json();
  },
  async getApprovalDiff(id: number) {
    const res = await fetch(`/api/v1/approvals/${id}/diff`);
    if (!res.ok) throw new Error('Failed to get diff');
    return res.json();
  },
  // ---- Tenant settings / policy ----
  async getTenantPolicy() {
    const res = await fetch(`/api/v1/tenant/settings`);
    if (!res.ok) throw new Error('Failed to load tenant policy');
    return res.json();
  },
  async updateTenantPolicy(payload: any) {
    const res = await fetch(`/api/v1/tenant/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(t || 'Failed to update tenant policy');
    }
    return res.json();
  },
  async testTenantPolicy(payload: { action_type: string; confidence: number; agent_name?: string }) {
    const res = await fetch(`/api/v1/tenant/settings/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to test policy');
    return res.json();
  },
  async postSessionAct(sessionId: string, action: any) {
    const res = await fetch(`/api/v1/odl/sessions/${encodeURIComponent(sessionId)}/act`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(action),
    });
    if (!res.ok) throw new Error('Failed to apply approved action');
    return res.json();
  },

  // --- Agents Catalog (MVP) ---
  listAgents: async (): Promise<
    Array<{ name: string; display_name?: string; version?: string; domain?: string; risk_class?: string; capabilities?: string[] }>
  > => {
    const res = await fetch(`${API_BASE_URL}/agents`);
    if (!res.ok) throw new Error('Failed to list agents');
    const data = await res.json();
    return Array.isArray(data) ? data : data?.agents ?? [];
  },
  getAgent: async (name: string): Promise<any> => {
    const res = await fetch(`${API_BASE_URL}/agents/${encodeURIComponent(name)}`);
    if (!res.ok) throw new Error(`Failed to get agent ${name}`);
    return res.json();
  },
  enableAgent: async (name: string): Promise<void> => {
    const res = await fetch(`${API_BASE_URL}/agents/${encodeURIComponent(name)}/enable`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to enable agent');
  },
  disableAgent: async (name: string): Promise<void> => {
    const res = await fetch(`${API_BASE_URL}/agents/${encodeURIComponent(name)}/disable`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to disable agent');
  },
  registerAgent: async (spec: any): Promise<void> => {
    const res = await fetch(`${API_BASE_URL}/agents/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(spec),
    });
    if (!res.ok) throw new Error('Failed to register agent');
  },

  /** Requirements status helper for blocked gather step. */
  async getRequirementsStatus(sessionId: string): Promise<{
    missing_requirements: string[];
    missing_components: string[];
    requirements_complete: boolean;
    components_available: boolean;
    can_proceed: boolean;
    graph_summary: string;
  }> {
    const res = await fetch(
      `${API_BASE_URL}/odl/sessions/${encodeURIComponent(sessionId)}/analysis`
    );
    if (!res.ok) throw new Error(`Requirements status failed: ${res.status}`);
    return res.json();
  },

  /** Get ODL text representation, with /view fallback */
    async getOdlText(
      sessionId: string,
      layer: string = 'single-line',
    ): Promise<{
      text?: string;
      version: number;
      node_count?: number;
      edge_count?: number;
      last_updated?: string;
    }> {
      const txt = await fetch(`${API_BASE_URL}/odl/sessions/${encodeURIComponent(sessionId)}/text`);
      if (txt.ok) return txt.json();
      if (txt.status === 404 || txt.status === 410) {
        const view = await fetch(
          `${API_BASE_URL}/odl/${encodeURIComponent(sessionId)}/view?layer=${encodeURIComponent(layer)}`
        );
        if (view.ok) {
          const data = await view.json();
          const nodes: Array<{ id: string; type?: string }> = data?.nodes ?? [];
          const edges: Array<{ source: string; target: string }> = data?.edges ?? [];
          const lines = [
            '# ODL (view fallback)',
            ...nodes.map(n => `node ${n.id}${n.type ? ` : ${n.type}` : ''}`),
            ...edges.map(e => `link ${e.source} -> ${e.target}`),
          ];
          return {
            text: lines.join('\n'),
            version: Number(data?.version ?? 0),
            node_count: nodes.length,
            edge_count: edges.length,
            last_updated: data?.last_updated,
          };
        }
        return { text: undefined, version: 0, node_count: 0, edge_count: 0 };
      }
      const t = await txt.text();
      throw new Error(`Get ODL text failed: ${txt.status} ${t}`);
    },

  /** Select component to replace placeholder */
  async selectComponent(sessionId: string, placeholderId: string, component: any): Promise<{
    success: boolean;
    message: string;
    replaced_nodes: string[];
    patch: any;
    updated_design_summary: string;
  }> {
    const res = await fetch(
      `${API_BASE_URL}/odl/sessions/${encodeURIComponent(sessionId)}/select-component`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          placeholder_id: placeholderId,
          component,
          apply_to_all_similar: false
        }),
      }
    );
    if (!res.ok) throw new Error(`Component selection failed: ${res.status}`);
    return res.json();
  },

  /** Get session versions */
  async getSessionVersions(sessionId: string): Promise<{
    session_id: string;
    versions: any[];
    total_versions: number;
  }> {
    const res = await fetch(`${API_BASE_URL}/odl/sessions/${encodeURIComponent(sessionId)}/versions`);
    if (!res.ok) throw new Error(`Get versions failed: ${res.status}`);
    return res.json();
  },
};

export async function planAndRun(sessionId: string, command: string): Promise<void> {
  const plan = await api.getPlanForSession(sessionId, command);
  const { runPlan } = await import('./runner');
  await runPlan(sessionId, plan as any);
}
