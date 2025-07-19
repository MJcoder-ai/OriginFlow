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
}

export type Route = 'projects' | 'components';

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

  /** Current route of the main panel. */
  route: Route;
  /** Navigate to a new route. */
  setRoute: (r: Route) => void;

  /** List of in-progress and completed uploads. */
  uploads: UploadEntry[];
  /** Add a new upload entry. */
  addUpload: (u: UploadEntry) => void;
  /** Update an existing upload entry. */
  updateUpload: (id: string, patch: Partial<UploadEntry>) => void;
  /** Fetch uploaded file assets. */
  loadUploads: () => Promise<void>;

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
  chatMode: 'default',
  isAiProcessing: false,
  route: 'projects',
  uploads: [],
  activeDatasheet: null,
  setActiveDatasheet: (data) => set({ activeDatasheet: data }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  selectComponent: (id) => set({ selectedComponentId: id }),
  async fetchProject() {
    set({ status: 'loading' });
    try {
      const [components, linksFromApi] = await Promise.all([
        api.getComponents(),
        api.getLinks(),
      ]);
      const enrichedComponents = components.map((c) => ({
        ...c,
        ports: [
          { id: 'input', type: 'in' },
          { id: 'output', type: 'out' },
        ],
      }));
      set({ canvasComponents: enrichedComponents, links: linksFromApi, status: 'ready' });
    } catch (error) {
      console.error('Failed to load project:', error);
      set({ status: 'Error: Could not load project' });
    }
  },
  async addComponent(payload) {
    set({ status: `Adding ${payload.type}...` });
    try {
      const saved = await api.createComponent(payload);
      const component: CanvasComponent = {
        ...saved,
        ports: [
          { id: 'input', type: 'in' },
          { id: 'output', type: 'out' },
        ],
      };
      set((state) => ({
        canvasComponents: [...state.canvasComponents, component],
        status: `Component ${saved.name} added`,
      }));
    } catch (error) {
      console.error('Failed to add component:', error);
      set({ status: 'Error: Could not add component' });
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
    try {
      const saved = await api.createLink({ source_id, target_id });
      set((state) => ({ links: [...state.links, saved], status: 'Link created' }));
    } catch (error) {
      console.error('Failed to add link:', error);
      set({ status: 'Error: Could not create link' });
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
        case 'suggestLink':
          set((s) => ({ ghostLinks: [...s.ghostLinks, act.payload] }));
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

    try {
      const snapshot = { components: canvasComponents, links };
      const actions = await api.analyzeDesign(snapshot, command);
      await executeAiActions(actions);

      // 2. Add AI success message
      const successMessage = `I have successfully executed ${actions.length} action(s).`;
      addMessage({ id: crypto.randomUUID(), author: 'AI', text: successMessage });
    } catch (error) {
      console.error('AI command failed:', error);
      const errorMessage = 'Sorry, I ran into an error trying to do that.';
      // 3. Add AI error message
      addMessage({ id: crypto.randomUUID(), author: 'AI', text: errorMessage });
      set({ status: 'Error: AI command failed' });
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
        })),
      });
    } catch (error) {
      console.error('Failed to load uploads', error);
    }
  },
}));

