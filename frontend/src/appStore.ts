/**
 * File: frontend/src/appStore.ts
 * Central Zustand store for application state management.
 * Tracks canvas components, links, and current selection.
 * Exposed via the `useAppStore` hook for React components.
 */
import { create } from 'zustand';
import { api } from './services/api';
import { listFiles } from './services/fileApi';
import { AiAction } from './types/ai';

export interface UploadEntry {
  id: string;
  name: string;
  size: number;
  mime: string;
  progress: number; // 0-100, 101 queued for AI, 200 done
  assetType?: 'component';
  parsed_at: string | null;
  parsing_status: 'pending' | 'processing' | 'success' | 'failed' | null;
  parsing_error: string | null;
  is_human_verified: boolean;
}

export type Route = 'projects' | 'components' | 'settings' | 'agents' | 'approvals' | 'policy';

/** Connection port available on a component. */
export interface Port {
  /** Port identifier, fixed to either 'input' or 'output'. */
  id: 'input' | 'output';
  /** Defines whether the port accepts or emits connections. */
  type: 'in' | 'out';
}

/**
 * Representation of a single component instance placed on the canvas.
 */
export interface CanvasComponent {
  /** Unique identifier for the component. */
  id: string;
  /** Display name presented in the UI. */
  name: string;
  /** Component type used for palette lookup. */
  type: string;
  /** Horizontal position on the canvas. */
  x: number;
  /** Vertical position on the canvas. */
  y: number;
  /** Connection ports available on the component. */
  ports: Port[];
  /**
   * Name of the layer this component belongs to. Components without a
   * layer are assumed to be part of the default Single-Line Diagram.
   */
  layer?: string;
}

/**
 * Universal shape for a chat message.
 */
export interface Message {
  id: string;
  author: 'User' | 'AI';
  text: string;
  /**
   * Optional rich card data associated with the message.  If present,
   * the chat UI will render a card instead of a plain text bubble.
   * Cards can contain component suggestions, bill of materials summaries
   * or other structured content with actions.  When `card` is defined
   * the `text` field should be considered a fallback/plain description.
   */
  card?: DesignCardData;
  /**
   * Optional message classification.  If set to 'status' the message
   * represents a system status update rather than a user/AI conversation
   * turn.  Card messages are implicitly classified as 'card'.
   */
  type?: 'text' | 'card' | 'status';
}

/**
 * Supported statuses for a plan task.  When a user asks the AI to
 * perform a complex operation, the orchestrator can break it into
 * discrete steps and populate the planTasks array with tasks
 * representing each stage of the workflow.  The frontend will
 * visualise this sequence in the chat sidebar.
 */
export type PlanTaskStatus = 'pending' | 'in_progress' | 'complete' | 'blocked';

/**
 * Representation of a single high‑level task in the AI's plan.
 */
export interface PlanTask {
  id: string;
  /** Short human‑readable title for the task. */
  title: string;
  /** Detailed description explaining the objective of the task. */
  description?: string;
  /** Current execution status. */
  status: PlanTaskStatus;
}

/**
 * Data structure for rendering rich design cards in the chat interface.
 * Cards present structured information about components or proposals
 * and can include a list of interactive actions.  The UI will
 * display the title, description, optional image and specs table.
 */
export interface DesignCardData {
  /** Title or headline for the card (e.g. component name). */
  title: string;
  /** Free‑form description or summary. */
  description?: string;
  /** URL for an image preview.  If omitted, a placeholder will be shown. */
  imageUrl?: string;
  /** Structured list of key/value specs to display in a table. */
  specs?: { label: string; value: string }[];
  /** List of suggested actions.  Each action will render as a button in the card. */
  actions?: { label: string; command: string; variant?: 'primary' | 'secondary' | 'danger' }[];
  /** Confidence score from the AI agent (0-1) */
  confidence?: number;
  /** Name of the agent that generated this card */
  agent?: string;
  /** Unique identifier for tracking feedback */
  cardId?: string;
  /** Alternative suggestions */
  alternatives?: Array<{
    title: string;
    description: string;
    confidence: number;
    command: string;
  }>;
}

/**
 * Representation of a connection between two canvas components.
 */
export interface Link {
  /** Unique identifier for this link. */
  id: string;
  /** Source component identifier. */
  source_id: string;
  /** Target component identifier. */
  target_id: string;
}

/**
 * Shape of the global application state managed by Zustand.
 */
type AppStatus = 'loading' | 'ready' | 'error' | 'saving' | string;

export type ChatMode = 'default' | 'dictating' | 'voice';

interface AppState {
  /** Components currently placed on the canvas. */
  canvasComponents: CanvasComponent[];
  /** Links connecting components on the canvas. */
  links: Link[];
  ghostLinks?: Link[];
  bomItems: string[] | null;
  /** The id of the currently selected component. */
  selectedComponentId: string | null;
  /** History of messages in the chat panel. */
  messages: Message[];

  /**
   * High‑level plan returned by the orchestrator.  When the user
   * requests a complex operation (e.g. “Design a 5 kW PV system”) the
   * orchestrator breaks it into tasks and populates this array.  The
   * UI visualises tasks in a timeline and updates their statuses as
   * they progress.
   */
  planTasks: PlanTask[];
  /** Replace the entire plan tasks list. */
  setPlanTasks: (tasks: PlanTask[]) => void;
  /** Update the status of a single task by id. */
  updatePlanTaskStatus: (id: string, status: PlanTaskStatus) => void;
  /** Clear all plan tasks. */
  clearPlanTasks: () => void;

  /** Unique design session identifier (default persists across reloads). */
  sessionId: string;
  setSessionId: (id: string) => void;

  /** Monotonic graph version for optimistic concurrency. */
  graphVersion: number;
  setGraphVersion: (version: number) => void;
  /**
   * Synchronise the local graph version with the server.
   *
   * Fetches the current design text and updates the graphVersion. Use
   * this after retrieving a plan to avoid initial 409 version conflicts.
   */
  syncGraphVersion: (sessionId: string) => Promise<void>;

  /**
   * Execute a plan task via the backend.  Sends the task to the
   * ``/odl/{session_id}/act`` endpoint, applies the returned patch,
   * shows any design card in the chat, and updates the task status.
  */
  performPlanTask: (task: PlanTask) => Promise<PlanTaskStatus>;
  /** User-provided requirements for gather phase. */
  requirements: { target_power?: number; roof_area?: number; budget?: number; brand?: string };
  updateRequirements: (patch: Partial<{ target_power: number; roof_area: number; budget: number; brand: string }>) => Promise<void>;


  /**
   * Suggested quick actions displayed beneath the chat input.  Each
   * action defines a user‑friendly label and a command string that
   * will be sent to the AI when clicked.  The orchestrator can
   * populate this list based on context and recent interactions.
   */
  quickActions: { id: string; label: string; command: string }[];
  /** Set the full quick actions list. */
  setQuickActions: (actions: { id: string; label: string; command: string }[]) => void;

  /**
   * Current high‑level chat mode.  Determines which tools are
   * available to the AI and influences how prompts are interpreted.
   * For example, 'design' mode allows multi‑file editing and system
   * design, whereas 'analyze' is read‑only.  'manual' restricts AI
   * modifications and 'business' is reserved for sales and CRM flows.
   */
  currentMode: 'design' | 'analyze' | 'manual' | 'business';
  /** Update the current chat mode. */
  setCurrentMode: (mode: 'design' | 'analyze' | 'manual' | 'business') => void;
  /** Last natural-language prompt sent to the AI. */
  lastPrompt: string;
  /** Update which component is selected. */
  /** The current status message for the UI. */
  status: AppStatus;
  statusMessages: { id: string; message: string; icon?: string }[];
  /** Add a status message with an optional icon. */
  addStatusMessage: (msg: string, icon?: string) => void;
  removeStatusMessage: (id: string) => void;
  selectComponent: (id: string | null) => void;
  /** Fetch the entire project from the backend API. */
  fetchProject: () => Promise<void>;
  /** Add a component to the canvas using a full payload. */
  addComponent: (payload: { name: string; type: string; standard_code: string; x?: number; y?: number }) => Promise<void>;
  /** Update a component's name by id. */
  updateComponentName: (componentId: string, newName: string) => Promise<void>;
  /** Offset a component's position by drag delta. */
  updateComponentPosition: (
    componentId: string,
    delta: { x: number; y: number }
  ) => Promise<void>;
  deleteComponent: (componentId: string) => Promise<void>;
  /** Register a new link between two components. */
  addLink: (
    link: {
      source_id: string;
      target_id: string;
    }
  ) => Promise<void>;
  /** Execute a list of AI-generated actions. */
  executeAiActions: (actions: AiAction[]) => Promise<void>;
  /** Apply previously approved AI actions immediately. */
  applyAiActions: (actions: AiAction[]) => Promise<void>;
  /** Send snapshot and command to AI and execute returned actions. */
  analyzeAndExecute: (command: string) => Promise<void>;
  setBom: (items: string[] | null) => void;

  /** Current mode of the chat input. */
  chatMode: ChatMode;
  /** Flag indicating whether the AI is processing a request. */
  isAiProcessing: boolean;
  /** Adds a message to the chat history. */
  addMessage: (message: Message) => void;
  /** Update chat mode. */
  setChatMode: (mode: ChatMode) => void;
  /** Update AI processing flag. */
  setIsAiProcessing: (isProcessing: boolean) => void;

  /** Draft text for the chat input */
  chatDraft: string;
  /** Update the chat draft */
  setChatDraft: (draft: string) => void;
  /** Clear the chat draft */
  clearChatDraft: () => void;

  /** Current route of the main panel. */
  route: Route;
  /** Navigate to a new route. */
  setRoute: (r: Route) => void;

  /** Visibility of the toolbar section */
  isSubNavVisible: boolean;
  /** Toggle toolbar visibility */
  toggleSubNav: () => void;

  /** Parsing settings controlling the backend pipeline. */
  useRuleBased: boolean;
  useTableExtraction: boolean;
  useAiExtraction: boolean;
  useOcrFallback: boolean;
  setExtractionSetting: (key: 'useRuleBased' | 'useTableExtraction' | 'useAiExtraction' | 'useOcrFallback', value: boolean) => void;

  /**
   * Canvas layers available for the current project. Each layer represents a distinct
   * view of the design (e.g. "Single-Line Diagram", "High-Level Overview").
   */
  layers: string[];
  /** The layer currently visible on the canvas. */
  currentLayer: string;
  /** Update the current layer. */
  setCurrentLayer: (layer: string) => void;

  // The ODL view reuses the main `sessionId`; no separate session tracking.


  /** Total cost of the current design, if estimated by the AI. */
  costTotal: number | null;
  /** Set the total cost estimate. */
  setCostTotal: (cost: number | null) => void;

  /** Estimated performance metrics such as annual energy output (kWh). */
  performanceMetrics: { annualKwh: number | null };
  /** Set performance metrics. */
  setPerformanceMetrics: (metrics: { annualKwh: number | null }) => void;

  /** Flag indicating whether the currently open datasheet has unsaved edits */
  datasheetDirty: boolean;
  /** Set the datasheet dirty flag. */
  setDatasheetDirty: (dirty: boolean) => void;

  /** History stack for undo/redo functionality.  Each entry
   *  represents a snapshot of the canvas components and links at a
   *  particular point in time.
   */
  history: { components: CanvasComponent[]; links: Link[] }[];
  /** Index of the current position in the history stack. */
  historyIndex: number;
  /** Record the current state before executing an action.  Truncates any
   *  redo history.
   */
  recordHistory: () => void;
  /** Undo the last approved action if possible. */
  undo: () => void;
  /** Redo the next action if possible. */
  redo: () => void;

  /** List of in-progress and completed uploads. */
  uploads: UploadEntry[];
  /** Add a new upload entry. */
  addUpload: (u: UploadEntry) => void;
  /** Update an existing upload entry. */
  updateUpload: (id: string, patch: Partial<UploadEntry>) => void;
  /** Fetch uploaded file assets. */
  loadUploads: () => Promise<void>;

  /** Voice command state. */
  voiceMode: 'idle' | 'listening' | 'processing' | 'speaking';
  /** Update voice command state. */
  setVoiceMode: (mode: 'idle' | 'listening' | 'processing' | 'speaking') => void;
  /** Continuous conversation flag. */
  isContinuousConversation: boolean;
  /** Toggle continuous conversation mode. */
  toggleContinuousConversation: () => void;

  /**
   * Current transcript captured from the microphone. This is updated with
   * interim results while listening and cleared when a final transcript
   * has been processed.
   */
  voiceTranscript: string;
  /** Whether speech synthesis is enabled for AI replies. */
  voiceOutputEnabled: boolean;
  /** Start listening for a voice command. */
  startListening: () => void;
  /** Stop listening. If a final transcript is provided it is submitted as a command. */
  stopListening: (finalTranscript?: string) => void;
  /** Update the interim voice transcript while listening. */
  updateVoiceTranscript: (text: string) => void;
  /** Toggle whether speech synthesis is enabled for AI replies. */
  toggleVoiceOutput: () => void;

  /** Currently opened datasheet split view */
  activeDatasheet: { url: string; payload: any; id: string } | null;
  setActiveDatasheet: (data: { url: string; payload: any; id: string } | null) => void;
}

/**
 * Create a Zustand store with basic component management helpers.
 */
export const useAppStore = create<AppState>((set, get) => ({
  canvasComponents: [],
  links: [],
  ghostLinks: [],
  bomItems: null,
  selectedComponentId: null,
  messages: [],
  // Current ODL session (persisted).
  sessionId: (typeof window !== 'undefined' && localStorage.getItem('of_session_id')) || 'global',
  setSessionId: (id: string) => {
    try {
      if (typeof window !== 'undefined') localStorage.setItem('of_session_id', id);
    } catch {}
    set({ sessionId: id });
  },
  /**
   * Current graph version returned by the backend.
   *
   * The graph version is used for optimistic concurrency when calling
   * POST /odl/sessions/{session_id}/act. The API will reject a request
   * with a 409 Conflict if the client's version is older than the
   * server's version. We initialise this to 0, but the store will
   * automatically synchronise it after the first plan fetch via
   * `syncGraphVersion`. Components should always read `graphVersion`
   * from the store rather than hard-coding 0.
   */
  graphVersion: 0,
  setGraphVersion: (version: number) => set({ graphVersion: version }),
  /**
   * Synchronise the local graph version with the server.
   *
   * This helper calls `/odl/sessions/{sessionId}/text` to fetch the
   * latest design representation (which includes the current version)
   * and updates the `graphVersion` state. It catches any errors and
   * logs them without interrupting the caller. Use this after
   * retrieving a plan to ensure the first call to `act` passes the
   * correct version and avoids an initial 409 conflict.
   */
  async syncGraphVersion(sessionId: string) {
    try {
      if (!sessionId) return;
      const { version } = await api.getOdlText(sessionId);
      if (typeof version === 'number') set({ graphVersion: version });
    } catch (e) {
      console.warn('Failed to sync graph version', e);
    }
  },
  // High‑level plan defaults to empty.  When the orchestrator
  // generates a plan it will replace this array.
  planTasks: [],
  setPlanTasks: (tasks) => set({ planTasks: tasks }),
  updatePlanTaskStatus: (id, status) =>
    set((s) => ({
      planTasks: s.planTasks.map((t) =>
        t.id === id ? { ...t, status } : t
      ),
    })),
  clearPlanTasks: () => set({ planTasks: [] }),

  async performPlanTask(task) {
    const sessionId = (get() as any).sessionId || 'global';
    // Helper to apply a graph patch to local state.
    const applyPatch = (patch: {
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
    }) => {
      if (!patch) return;
      if (patch.add_nodes) {
        set((s) => ({
          canvasComponents: [
            ...s.canvasComponents,
            ...patch.add_nodes.map((n: any) => ({
              id: n.id,
              name: n.data?.label ?? n.type,
              type: n.type,
              x: Math.random() * 500,
              y: Math.random() * 300,
              ports: [
                { id: 'input', type: 'in' },
                { id: 'output', type: 'out' },
              ],
            })),
          ],
        }));
      }
      if (patch.add_edges) {
        set((s) => ({
          links: [
            ...s.links,
            ...patch.add_edges.map((e: any) => ({
              id: `${e.source}_${e.target}_${crypto.randomUUID()}`,
              source_id: e.source,
              target_id: e.target,
            })),
          ],
        }));
      }
      const removeNodes = patch.remove_nodes ?? patch.removed_nodes;
      if (removeNodes && removeNodes.length) {
        set((s) => ({
          canvasComponents: s.canvasComponents.filter((c) => !removeNodes.includes(c.id)),
          links: s.links.filter(
            (l) => !removeNodes.includes(l.source_id) && !removeNodes.includes(l.target_id)
          ),
        }));
      }
      const removeEdges = patch.remove_edges ?? patch.removed_edges;
      if (removeEdges && removeEdges.length) {
        set((s) => ({
          links: s.links.filter(
            (l) => !removeEdges.some((e: any) => e.source === l.source_id && e.target === l.target_id)
          ),
        }));
      }
    };

    const execute = async (retry = false): Promise<PlanTaskStatus> => {
      try {
        const { patch, card, status, version } = await api.act(
          sessionId,
          task.id,
          undefined,
          get().graphVersion
        );
        if (typeof version === 'number') set({ graphVersion: version });
        applyPatch(patch);
        if (card) {
          get().addMessage({
            id: crypto.randomUUID(),
            author: 'AI',
            text: card.title,
            card: {
              title: card.title,
              description: card.description,
              imageUrl: (card as any).image_url,
              specs: card.specs?.map((s: any) => ({ label: s.label, value: s.value })),
              actions: card.actions?.map((a: any) => ({ label: a.label, command: a.command })),
            },
            type: 'card',
          });
        }
        const newStatus = (status as PlanTaskStatus) || 'complete';
        get().updatePlanTaskStatus(task.id, newStatus);

        // After completing a task, refresh the plan from the server to ensure the UI
        // reflects the latest list of tasks.  This prevents stale or duplicate tasks
        // from persisting in the timeline when the backend updates the plan.
        try {
          const refreshedPlan = await api.getPlanForSession(
            sessionId,
            get().lastPrompt || 'design'
          );
          if (
            (refreshedPlan as any).tasks &&
            Array.isArray((refreshedPlan as any).tasks)
          ) {
            set({ planTasks: (refreshedPlan as any).tasks as any });
          }
          // After refreshing the plan, synchronise the graph version so that
          // subsequent act requests carry the correct version number.
          await (get() as any).syncGraphVersion(sessionId);
        } catch (e) {
          console.warn('Failed to refresh plan after act', e);
        }

        return newStatus;
      } catch (err: any) {
        if (!retry && err.status === 409) {
          get().addStatusMessage('The design has changed—refreshing…', 'warning');
          let serverVersion: number | undefined;
          const match = String(err.detail || '').match(/server has (\d+)/);
          if (match) serverVersion = parseInt(match[1], 10);
          if (serverVersion !== undefined) {
            set({ graphVersion: serverVersion });
          }
          try {
            const plan = await api.getPlanForSession(sessionId, get().lastPrompt || 'design');
            if ((plan as any).tasks && Array.isArray((plan as any).tasks))
              set({ planTasks: (plan as any).tasks as any });
            // After refetching the plan, sync the graph version to avoid
            // another conflict when we retry the act call.
            await (get() as any).syncGraphVersion(sessionId);
          } catch (_) {}
          return await execute(true);
        }
        console.error('Failed to perform plan task', err);
        get().updatePlanTaskStatus(task.id, 'blocked');
        get().addStatusMessage('Failed to perform task', 'error');
        return 'blocked';
      }
    };

    get().updatePlanTaskStatus(task.id, 'in_progress');
    set({ isAiProcessing: true });
    try {
      return await execute(false);
    } finally {
      set({ isAiProcessing: false });
    }
  },
  // Requirements sync
  requirements: {},
  async updateRequirements(patch) {
    const next = { ...get().requirements, ...patch } as any;
    set({ requirements: next });
    try {
      const sessionId = get().sessionId;
      if (sessionId) await api.postRequirements(sessionId, next);
      if (sessionId) {
        const plan = await api.getPlanForSession(sessionId, get().lastPrompt || 'design');
        if ((plan as any).tasks && Array.isArray((plan as any).tasks)) {
          set({ planTasks: (plan as any).tasks as any });
        }
        // Synchronise graph version after fetching the plan so the next act call uses the correct version.
        await (get() as any).syncGraphVersion(sessionId);
      }
    } catch (e) {
      console.error('Failed to update requirements', e);
    }
  },

  // Quick actions and mode selection defaults
  quickActions: [],
  setQuickActions: (actions) => set({ quickActions: actions }),
  currentMode: 'design',
  setCurrentMode: (mode) => set({ currentMode: mode }),
  lastPrompt: '',
  status: 'loading',
  statusMessages: [],
  chatMode: 'default',
  isAiProcessing: false,
  // Cost and performance estimations.  These values are populated when the AI
  // returns rough cost or performance estimates (e.g. via the financial or
  // performance agents).  A value of null indicates that no estimate is
  // available.  These can be displayed in the status bar or dedicated
  // panels.
  costTotal: null,
  setCostTotal: (cost) => set({ costTotal: cost }),
  performanceMetrics: { annualKwh: null },
  setPerformanceMetrics: (metrics) => set({ performanceMetrics: metrics }),

  // Flag indicating whether the currently open datasheet has unsaved edits
  // or pending confirmations. Used by the toolbar to enable Confirm & Close.
  datasheetDirty: false,
  setDatasheetDirty: (dirty: boolean) => set({ datasheetDirty: dirty }),

  // History for undo/redo: start with empty list and no index
  history: [],
  historyIndex: -1,
  recordHistory: () => {
    const state = get();
    // Deep copy components and links to avoid mutation
    const snapshot = {
      components: state.canvasComponents.map((c) => ({ ...c })),
      links: state.links.map((l) => ({ ...l })),
    };
    set((s) => {
      const trimmed = s.history.slice(0, s.historyIndex + 1);
      return {
        history: [...trimmed, snapshot],
        historyIndex: trimmed.length,
      };
    });
  },
  undo: () => {
    const state = get();
    if (state.historyIndex <= 0) return;
    const newIndex = state.historyIndex - 1;
    const snapshot = state.history[newIndex];
    if (!snapshot) return;
    set({
      canvasComponents: snapshot.components.map((c) => ({ ...c })),
      links: snapshot.links.map((l) => ({ ...l })),
      historyIndex: newIndex,
    });
  },
  redo: () => {
    const state = get();
    if (state.historyIndex < 0 || state.historyIndex >= state.history.length - 1) return;
    const newIndex = state.historyIndex + 1;
    const snapshot = state.history[newIndex];
    if (!snapshot) return;
    set({
      canvasComponents: snapshot.components.map((c) => ({ ...c })),
      links: snapshot.links.map((l) => ({ ...l })),
      historyIndex: newIndex,
    });
  },
  route: 'projects',
  isSubNavVisible: true,
  uploads: [],
  // Default extraction settings. These flags control how the backend parses
  // datasheets. They match the toggles in the Settings panel.
  useRuleBased: true,
  useTableExtraction: true,
  useAiExtraction: true,
  useOcrFallback: false,

  // Layer management defaults.  Each project starts with four layers.
  layers: [
    'Single-Line Diagram',
    'High-Level Overview',
    'Civil/Structural',
    'Networking/Monitoring',
    'ODL Code',
  ],
  currentLayer: 'Single-Line Diagram',
  setCurrentLayer: (layer) => {
    set({ currentLayer: layer });
    
    // When switching layers we no longer auto-create a separate ODL session.
    // The "ODL Code" layer reads the same session used for design tasks.
  },

  // The ODL view now reuses `sessionId` directly.

  voiceMode: 'idle',
  isContinuousConversation: false,
  voiceTranscript: '',
  voiceOutputEnabled: false,
  chatDraft: '',
  activeDatasheet: null,
  setActiveDatasheet: (data) => set({ activeDatasheet: data }),
  setVoiceMode: (mode) => set({ voiceMode: mode }),
  toggleContinuousConversation: () =>
    set((s) => ({ isContinuousConversation: !s.isContinuousConversation })),

  startListening: () => {
    set({ voiceTranscript: '', voiceMode: 'listening' });
  },

  stopListening: (finalTranscript?: string) => {
    set({ voiceMode: 'idle', voiceTranscript: '' });
    if (finalTranscript && finalTranscript.trim()) {
      get().analyzeAndExecute(finalTranscript.trim());
    }
  },

  updateVoiceTranscript: (text) => set({ voiceTranscript: text }),

  toggleVoiceOutput: () =>
    set((s) => ({ voiceOutputEnabled: !s.voiceOutputEnabled })),
  setChatDraft: (draft) => set({ chatDraft: draft }),
  clearChatDraft: () => set({ chatDraft: '' }),
  toggleSubNav: () => set((s) => ({ isSubNavVisible: !s.isSubNavVisible })),
  // Update a parsing flag by key. The key must be one of the
  // four extraction settings defined above.
  setExtractionSetting: (key, value) =>
    set((s) => ({ ...s, [key]: value })),
  addStatusMessage: (msg, icon) =>
    set((s) => ({
      statusMessages: [
        ...s.statusMessages,
        { id: crypto.randomUUID(), message: msg, icon },
      ],
    })),
  removeStatusMessage: (id) =>
    set((s) => ({ statusMessages: s.statusMessages.filter((m) => m.id !== id) })),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  selectComponent: (id) => set({ selectedComponentId: id }),
  async fetchProject() {
    set({ status: 'loading' });
    get().addStatusMessage('Loading project...', 'info');
    try {
      const [components, linksFromApi] = await Promise.all([
        api.getComponents(),
        api.getLinks(),
      ]);
      const enrichedComponents = components.map((c) => ({
        ...c,
        // Preserve existing layer if defined, otherwise default to the first layer
        layer: (c as any).layer ?? 'Single-Line Diagram',
        ports: [
          { id: 'input', type: 'in' },
          { id: 'output', type: 'out' },
        ],
      }));
      set({ canvasComponents: enrichedComponents, links: linksFromApi, status: 'ready' });
      get().addStatusMessage('Project loaded', 'success');
    } catch (error) {
      console.error('Failed to load project:', error);
      set({ status: 'Error: Could not load project' });
      get().addStatusMessage('Failed to load project', 'error');
    }
  },
  async addComponent(payload) {
    set({ status: `Adding ${payload.type}...` });
    get().addStatusMessage(`Adding ${payload.type}...`, 'info');
    try {
      // Ensure the backend receives the layer information so it can be persisted.
      const payloadWithLayer = { ...payload, layer: get().currentLayer };
      const saved = await api.createComponent(payloadWithLayer);
      const component: CanvasComponent = {
        ...saved,
        ports: [
          { id: 'input', type: 'in' },
          { id: 'output', type: 'out' },
        ],
        layer: get().currentLayer,
      };
      set((state) => ({
        canvasComponents: [...state.canvasComponents, component],
        status: `Component ${saved.name} added`,
      }));
      get().addStatusMessage(`Component ${saved.name} added`, 'success');
    } catch (error) {
      console.error('Failed to add component:', error);
      set({ status: 'Error: Could not add component' });
      get().addStatusMessage('Failed to add component', 'error');
    }
  },
  async updateComponentName(componentId, newName) {
    const components = get().canvasComponents;
    const updated = components.map((c) =>
      c.id === componentId ? { ...c, name: newName } : c
    );
    set({ canvasComponents: updated });
    try {
      await api.updateComponent(componentId, { name: newName });
    } catch (error) {
      console.error('Failed to update component name:', error);
      set({ canvasComponents: components });
    }
  },

  async updateComponentPosition(componentId, delta) {
    const originalComponents = get().canvasComponents;
    const component = originalComponents.find((c) => c.id === componentId);
    if (!component) return;

    const newX = Math.round(component.x + delta.x);
    const newY = Math.round(component.y + delta.y);
    const updatedComponent = {
      ...component,
      x: newX,
      y: newY,
    };
    set({
      canvasComponents: originalComponents.map((c) =>
        c.id === componentId ? updatedComponent : c
      ),
    });
    try {
      await api.updateComponent(componentId, {
        x: newX,
        y: newY,
      });
    } catch (error) {
      console.error('Failed to save new position:', error);
      // Revert on failure
      set({ canvasComponents: originalComponents });
    }
  },

  async deleteComponent(componentId) {
    set((state) => ({
      canvasComponents: state.canvasComponents.filter((c) => c.id !== componentId),
      links: state.links.filter(
        (l) => l.source_id !== componentId && l.target_id !== componentId
      ),
      selectedComponentId: null,
    }));
    try {
      await api.deleteComponent(componentId);
    } catch (error) {
      console.error('Failed to delete component:', error);
      get().fetchProject();
    }
  },
  async addLink({ source_id, target_id }) {
    const linkExists = get().links.some(
      (l) => l.source_id === source_id && l.target_id === target_id
    );
    if (linkExists || source_id === target_id) {
      return;
    }
    set({ status: 'Creating link...' });
    get().addStatusMessage('Creating link...', 'info');
    try {
      const saved = await api.createLink({ source_id, target_id });
      set((state) => ({ links: [...state.links, saved], status: 'Link created' }));
      get().addStatusMessage('Link created', 'success');
    } catch (error) {
      console.error('Failed to add link:', error);
      set({ status: 'Error: Could not create link' });
      get().addStatusMessage('Failed to create link', 'error');
    }
  },

  async executeAiActions(actions) {
    // In plan–act mode, execute all modifications immediately.
    const applyNow: AiAction[] = [];
    for (const action of actions) {
      switch (action.action) {
        case 'addComponent':
        case 'addLink':
        case 'removeComponent':
        case 'updatePosition':
        case 'suggestLink':
          applyNow.push(action);
          break;
        case 'validation': {
          const msg = (action.payload as any)?.message;
          if (msg) {
            get().addMessage({ id: crypto.randomUUID(), author: 'AI', text: msg });
          }
          break;
        }
        case 'report': {
          get().setBom((action.payload as any).items);
          break;
        }
        default:
          console.error('AI action not implemented', action);
      }
    }
    if (applyNow.length > 0) {
      // Record history for undo/redo
      get().recordHistory();
      await get().applyAiActions(applyNow);
      get().addMessage({
        id: crypto.randomUUID(),
        author: 'AI',
        text: `✅ Applied ${applyNow.length} action(s) automatically.`,
      });
    }
  },

  async applyAiActions(actions) {
    for (const act of actions) {
      switch (act.action) {
        case 'addComponent':
          await get().addComponent(act.payload);
          break;
        case 'removeComponent':
          await get().deleteComponent(act.payload.id);
          break;
        case 'addLink':
          await get().addLink(act.payload);
          break;
        case 'suggestLink': {
          const { source_name, target_name, source_id, target_id } = act.payload as any;
          const comps = get().canvasComponents;
          let srcComp = comps.find((c) => source_name && c.name === source_name);
          let tgtComp = comps.find((c) => target_name && c.name === target_name);
          if (!srcComp && source_id) srcComp = comps.find((c) => c.id === source_id);
          if (!tgtComp && target_id) tgtComp = comps.find((c) => c.id === target_id);
          if (srcComp && tgtComp) {
            try {
              await get().addLink({ source_id: srcComp.id, target_id: tgtComp.id });
            } catch (e) {
              console.error('Failed to create link from suggestion', e);
              set((s) => ({ ghostLinks: [...s.ghostLinks, act.payload] }));
            }
          } else {
            set((s) => ({ ghostLinks: [...s.ghostLinks, act.payload] }));
          }
          break;
        }
        case 'updatePosition':
          set((s) => ({
            canvasComponents: s.canvasComponents.map((c) =>
              c.id === act.payload.id
                ? { ...c, x: act.payload.x, y: act.payload.y }
                : c,
            ),
          }));
          break;
        case 'report':
          get().setBom(act.payload.items);
          break;
        default:
          console.warn('AI action not implemented', act);
      }
    }
  },

  async analyzeAndExecute(command) {
    const { addMessage, setIsAiProcessing, setPlanTasks, setQuickActions } = get();
    set({ lastPrompt: command });
    // Announce command and mark AI busy
    addMessage({ id: crypto.randomUUID(), author: 'User', text: command });
    setIsAiProcessing(true);
    get().addStatusMessage('Processing command', 'info');

    (async () => {
      try {
        const sessionId = (get() as any).sessionId || 'global';
        // Ensure session exists
        try {
          const created = await api.createOdlSession(sessionId !== 'global' ? sessionId : undefined);
          if (created?.session_id) get().setSessionId(created.session_id);
        } catch (err) {
          console.warn('ODL session init failed', err);
        }
        // Request a plan for this session
        const plan = await api.getPlanForSession(get().sessionId, command);
        // Sync the graph version so the first act call uses the current version
        await (get() as any).syncGraphVersion(get().sessionId);
        if (plan.tasks && Array.isArray(plan.tasks)) {
          // Merge new tasks with existing ones, preserving their statuses
          const existingTasks = get().planTasks;
          const merged: PlanTask[] = plan.tasks.map((t: any) => {
            const existing = existingTasks.find((et) => et.id === t.id);
            return {
              id: t.id,
              title: t.title,
              description: t.description,
              status: existing ? existing.status : ((t.status ?? 'pending') as any),
            };
          });
          setPlanTasks(merged);
        }
        if (plan.quick_actions && Array.isArray(plan.quick_actions)) {
          setQuickActions(
            plan.quick_actions.map((qa: any) => ({
              id: qa.id,
              label: qa.label,
              command: qa.command,
            }))
          );
        }
        // Execute each plan task automatically via act endpoint
        if (plan.tasks && Array.isArray(plan.tasks)) {
          for (const t of plan.tasks) {
            const status = await get().performPlanTask({
              id: t.id,
              title: t.title,
              description: t.description,
              status: (t.status ?? 'pending') as any,
            } as any);
            if (status === 'blocked') break;
          }
        }
      } catch (err) {
        console.error('Failed to load plan', err);
      }
    })();
    try {
      const { canvasComponents, links } = get();
      const snapshot = { components: canvasComponents, links };
      /*
       * Send every command through the analysis route.  The router agent will
       * classify the intent (design vs. component vs. wiring, etc.) and return
       * one or more AiActions.  Removing the old substring check on “design”
       * allows natural‑language requests like “add another solar panel to this
       * design” to be handled by the component_agent instead of being
       * mis‑routed to the planner.
       */
      let actions: AiAction[] = [];
      actions = await api.analyzeDesign(snapshot, command);
      if (actions.length > 0) {
        await get().executeAiActions(actions);
      }
    } catch (err) {
      console.error('Failed to analyze design', err);
      get().addStatusMessage('Failed to perform actions', 'error');
    } finally {
      setIsAiProcessing(false);
    }
  },
  setBom(items) {
    set({ bomItems: items });
  },
  setChatMode(mode) {
    set({ chatMode: mode });
  },
  setIsAiProcessing(isProcessing) {
    set({ isAiProcessing: isProcessing });
  },
  setRoute(r) {
    set({ route: r });
  },
  addUpload(u) {
    set((s) => ({ uploads: [...s.uploads, u] }));
  },
  updateUpload(id, patch) {
    set((s) => ({
      uploads: s.uploads.map((u) => (u.id === id ? { ...u, ...patch } : u)),
    }));
  },
  async loadUploads() {
    try {
      const assets = await listFiles();
      set({
        uploads: assets.map((a) => ({
          id: a.id,
          name: a.filename,
          size: a.size,
          mime: a.mime,
          progress: 101,
          assetType: 'component',
          parsed_at: a.parsed_at,
          parsing_status: a.parsing_status ?? null,
          parsing_error: a.parsing_error ?? null,
          is_human_verified: a.is_human_verified ?? false,
        })),
      });
    } catch (error) {
      console.error('Failed to load uploads', error);
    }
  },
}));

