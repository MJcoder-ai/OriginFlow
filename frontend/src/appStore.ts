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
  /** Source component and port. */
  source: { componentId: string; portId: 'output' };
  /** Target component and port. */
  target: { componentId: string; portId: 'input' };
}

/**
 * Shape of the global application state managed by Zustand.
 */
interface AppState {
  /** Flag indicating whether data is being loaded from the API. */
  isLoading: boolean;
  /** Components currently placed on the canvas. */
  canvasComponents: CanvasComponent[];
  /** Links connecting components on the canvas. */
  links: Link[];
  /** The id of the currently selected component. */
  selectedComponentId: string | null;
  /** Update which component is selected. */
  selectComponent: (id: string | null) => void;
  /** Fetch the entire project from the backend API. */
  fetchProject: () => Promise<void>;
  /** Add a component to the canvas using its type. */
  addComponent: (componentType: string) => Promise<void>;
  /** Update a component's name by id. */
  updateComponentName: (componentId: string, newName: string) => void;
  /** Offset a component's position by drag delta. */
  updateComponentPosition: (
    componentId: string,
    delta: { x: number; y: number }
  ) => void;
  /** Register a new link between two components. */
  addLink: (
    link: {
      source: { componentId: string; portId: 'output' };
      target: { componentId: string; portId: 'input' };
    }
  ) => Promise<void>;
}

/**
 * Create a Zustand store with basic component management helpers.
 */
export const useAppStore = create<AppState>((set, get) => ({
  isLoading: true,
  canvasComponents: [],
  links: [],
  selectedComponentId: null,
  selectComponent: (id) => set({ selectedComponentId: id }),
  async fetchProject() {
    set({ isLoading: true });
    try {
      const [components, links] = await Promise.all([
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
      set({ canvasComponents: enrichedComponents, links, isLoading: false });
    } catch (error) {
      console.error('Failed to load project:', error);
      set({ isLoading: false });
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
      }));
    } catch (error) {
      console.error('Failed to add component:', error);
    }
  },
  updateComponentName: (componentId, newName) =>
    set((state) => ({
      canvasComponents: state.canvasComponents.map((component) =>
        component.id === componentId ? { ...component, name: newName } : component
      ),
    })),
  updateComponentPosition: (componentId, delta) =>
    set((state) => ({
      canvasComponents: state.canvasComponents.map((component) =>
        component.id === componentId
          ? { ...component, x: component.x + delta.x, y: component.y + delta.y }
          : component
      ),
    })),
  async addLink({ source, target }) {
    const linkExists = get().links.some(
      (l) =>
        l.source.componentId === source.componentId &&
        l.target.componentId === target.componentId
    );
    if (linkExists || source.componentId === target.componentId) {
      return;
    }
    try {
      const saved = await api.createLink({
        source_id: source.componentId,
        target_id: target.componentId,
      });
      const newLink: Link = {
        id: saved.id,
        source,
        target,
      };
      set((state) => ({ links: [...state.links, newLink] }));
    } catch (error) {
      console.error('Failed to add link:', error);
    }
  },
}));

