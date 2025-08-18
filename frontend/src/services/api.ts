/**
 * File: frontend/src/services/api.ts
 * Centralized service for making API calls to the backend.
 * Provides helper functions to fetch and persist canvas data.
 */
import { CanvasComponent, Link, PlanTask } from '../appStore';
import { AiAction } from '../types/ai';
import { DesignSnapshot } from '../types/analysis';
import { API_BASE_URL } from '../config';

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

  async analyzeDesign(snapshot: DesignSnapshot, command: string): Promise<AiAction[]> {
    const res = await fetch(`${API_BASE_URL}/ai/analyze-design`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command, snapshot }),
    });
    if (!res.ok) throw new Error(`Analyze failed: ${res.status}`);
    return res.json();
  },

  /** Execute a plan task or quick action for an ODL session. */
  async act(
    sessionId: string,
    taskId: string,
    action?: string,
    graphVersion?: number,
  ): Promise<TaskExecutionResponse> {
    const res = await fetch(`${API_BASE_URL}/odl/sessions/${encodeURIComponent(sessionId)}/act`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // Include both the legacy `graph_version` and new `version` keys for
      // optimistic concurrency. The backend will prefer `version` but accepts
      // `graph_version` for backwards compatibility.
      body: JSON.stringify({
        task_id: taskId,
        action,
        version: graphVersion,
        graph_version: graphVersion,
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
  },

  /**
   * Create or reset an ODL design session.  Must be called before
   * using `/odl/sessions/{session_id}/plan` or `/odl/sessions/{session_id}/act`.
   */
  async createOdlSession(sessionId?: string): Promise<{ session_id: string }> {
    const res = await fetch(`${API_BASE_URL}/odl/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sessionId ? { session_id: sessionId } : {}),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Create session error ${res.status}: ${text.slice(0, 200)}`);
    }
    return res.json();
  },

  /**
   * Get a plan tailored to a specific ODL session.  Uses
   * `/odl/sessions/{session_id}/plan` to return tasks and quick actions
   * appropriate for the current graph.
   */
  async getPlanForSession(
    sessionId: string,
    command: string,
  ): Promise<{ tasks: any[]; quick_actions?: any[] }> {
    const res = await fetch(
      `${API_BASE_URL}/odl/sessions/${encodeURIComponent(sessionId)}/plan?command=${encodeURIComponent(
        command
      )}`
    );
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Plan session error ${res.status}: ${text.slice(0, 200)}`);
    }
    const data = await res.json();
    // Backend may return a plain array of tasks; normalize to an object
    if (Array.isArray(data)) {
      return { tasks: data } as any;
    }
    return data;
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

  /** Get ODL text representation */
  async getOdlText(sessionId: string): Promise<{
    text: string;
    version: number;
    node_count: number;
    edge_count: number;
    last_updated?: string;
  }> {
    const res = await fetch(`${API_BASE_URL}/odl/sessions/${encodeURIComponent(sessionId)}/text`);
    if (!res.ok) throw new Error(`Get ODL text failed: ${res.status}`);
    return res.json();
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