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

export type Route = 'projects' | 'components' | 'settings';

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

  /**
   * Queue of AI-generated actions awaiting user approval. These are surfaced
   * in the checklist UI so the user can approve or reject each one.
   */
  pendingActions: AiAction[];
  /** Add multiple pending actions to the queue. */
  addPendingActions: (actions: AiAction[]) => void;
  /** Approve a pending action by index and execute it. */
  approvePendingAction: (index: number) => Promise<void>;
  /** Reject a pending action by index. */
  rejectPendingAction: (index: number) => void;

  /** Running total cost of the current design.  This will be updated by
   *  financial agents in future phases; for now it can be set or
   *  incremented manually.  Displayed in the status bar.
   */
  costTotal: number;
  /** Update the total cost displayed in the status bar. */
  setCostTotal: (value: number) => void;

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
  status: 'loading',
  statusMessages: [],
  chatMode: 'default',
  isAiProcessing: false,
  // Cost tracking: initial total cost is zero
  costTotal: 0,
  setCostTotal: (value) => set({ costTotal: value }),

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
  ],
  currentLayer: 'Single-Line Diagram',

  // Pending AI actions awaiting user confirmation
  pendingActions: [],
  setCurrentLayer: (layer) => set({ currentLayer: layer }),
  addPendingActions: (actions) =>
    set((s) => ({ pendingActions: [...s.pendingActions, ...actions] })),
  approvePendingAction: async (index) => {
    const actions = get().pendingActions;
    const action = actions[index];
    if (!action) return;
    // Record history before applying the approved action
    get().recordHistory();
    await get().executeAiActions([action]);
    set((s) => ({ pendingActions: s.pendingActions.filter((_, i) => i !== index) }));
  },
  rejectPendingAction: (index) =>
    set((s) => ({ pendingActions: s.pendingActions.filter((_, i) => i !== index) })),
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
    for (const act of actions) {
      switch (act.action) {
        case 'addComponent':
          await get().addComponent(act.payload);
          break;
        case 'removeComponent':
          await get().deleteComponent(act.payload.id);
          break;
        case 'addLink':
          await api.createLink(act.payload);
          break;
        case 'suggestLink': {
          // Resolve names to IDs. Support new source_name/target_name fields as
          // well as legacy source_id/target_id fields (which may still contain
          // names). If either component cannot be found, store the link as a
          // ghost link to be resolved later.
          const payload: any = act.payload;
          const sourceName = payload.source_name ?? payload.source_id;
          const targetName = payload.target_name ?? payload.target_id;
          const src = get().canvasComponents.find((c) => c.name === sourceName);
          const tgt = get().canvasComponents.find((c) => c.name === targetName);
          if (src && tgt) {
            await get().addLink({ source_id: src.id, target_id: tgt.id });
          } else {
            set((s) => ({ ghostLinks: [...s.ghostLinks, act.payload] }));
          }
          break;
        }
          break;
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
    const { addMessage, setIsAiProcessing, executeAiActions, canvasComponents, links } = get();

    // 1. Add user message and set processing state
    addMessage({ id: crypto.randomUUID(), author: 'User', text: command });
    setIsAiProcessing(true);
    get().addStatusMessage('Processing command', 'info');

    try {
      const snapshot = { components: canvasComponents, links };
      const actions = await api.analyzeDesign(snapshot, command);
      // Separate actions into immediate (validation/report) and pending.
      const pending: AiAction[] = [];
      actions.forEach((action) => {
        switch (action.action) {
          case 'validation':
            if (action.payload && (action.payload as any).message) {
              addMessage({ id: crypto.randomUUID(), author: 'AI', text: (action.payload as any).message });
            }
            break;
          case 'report':
            if (action.payload && (action.payload as any).items) {
              get().setBom((action.payload as any).items);
              addMessage({ id: crypto.randomUUID(), author: 'AI', text: 'Here is your bill of materials.' });
            }
            break;
          default:
            pending.push(action);
            break;
        }
      });
      if (pending.length > 0) {
        get().addPendingActions(pending);
        const summaryMsg = `I have prepared ${pending.length} action(s) for your approval.`;
        addMessage({ id: crypto.randomUUID(), author: 'AI', text: summaryMsg });
        get().addStatusMessage('Actions awaiting approval', 'info');
      } else if (actions.length === 0) {
        addMessage({ id: crypto.randomUUID(), author: 'AI', text: 'I did not generate any actions for that command.' });
      }
    } catch (error) {
      console.error('AI command failed:', error);
      const errorMessage = 'Sorry, I ran into an error trying to do that.';
      // 3. Add AI error message
      addMessage({ id: crypto.randomUUID(), author: 'AI', text: errorMessage });
      set({ status: 'Error: AI command failed' });
      get().addStatusMessage('AI command failed', 'error');
    } finally {
      // 4. Reset processing state
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

