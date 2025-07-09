/**
 * File: frontend/src/appStore.ts
 * Central Zustand store for application state management.
 * Tracks canvas components, links, and current selection.
 * Exposed via the `useAppStore` hook for React components.
 */
import { create } from 'zustand';
import { api } from './services/api';

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

interface AppState {
  /** Components currently placed on the canvas. */
  canvasComponents: CanvasComponent[];
  /** Links connecting components on the canvas. */
  links: Link[];
  /** The id of the currently selected component. */
  selectedComponentId: string | null;
  /** Update which component is selected. */
  /** The current status message for the UI. */
  status: AppStatus;
  selectComponent: (id: string | null) => void;
  /** Fetch the entire project from the backend API. */
  fetchProject: () => Promise<void>;
  /** Add a component to the canvas using its type. */
  addComponent: (componentType: string) => Promise<void>;
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
}

/**
 * Create a Zustand store with basic component management helpers.
 */
export const useAppStore = create<AppState>((set, get) => ({
  canvasComponents: [],
  links: [],
  selectedComponentId: null,
  status: 'loading',
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
  async addComponent(componentType) {
    const newComponentData = {
      name: `${componentType} ${get().canvasComponents.length + 1}`,
      type: componentType,
      standard_code: `CODE-${Date.now()}`,
      x: 100,
      y: 100,
    };
    set({ status: `Adding ${componentType}...` });
    try {
      const saved = await api.createComponent(newComponentData);
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

    const updatedComponent = {
      ...component,
      x: component.x + delta.x,
      y: component.y + delta.y,
    };
    set({
      canvasComponents: originalComponents.map((c) =>
        c.id === componentId ? updatedComponent : c
      ),
    });
    try {
      await api.updateComponent(componentId, {
        x: updatedComponent.x,
        y: updatedComponent.y,
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
}));

