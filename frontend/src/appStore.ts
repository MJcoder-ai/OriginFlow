/**
 * File: frontend/src/appStore.ts
 * Central Zustand store for application state management.
 * Tracks canvas components, links, and current selection.
 * Exposed via the `useAppStore` hook for React components.
 */
import { create } from 'zustand';

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
  /** Components currently placed on the canvas. */
  canvasComponents: CanvasComponent[];
  /** Links connecting components on the canvas. */
  links: Link[];
  /** The id of the currently selected component. */
  selectedComponentId: string | null;
  /** Update which component is selected. */
  selectComponent: (id: string | null) => void;
  /** Add a component to the canvas using its type. */
  addComponent: (componentType: string) => void;
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
  ) => void;
}

/**
 * Create a Zustand store with basic component management helpers.
 */
export const useAppStore = create<AppState>((set) => ({
  canvasComponents: [],
  links: [],
  selectedComponentId: null,
  selectComponent: (id) => set({ selectedComponentId: id }),
  addComponent: (componentType) =>
    set((state) => {
      const newComponent: CanvasComponent = {
        id: `component_${Date.now()}`,
        name: `${componentType} ${state.canvasComponents.length + 1}`,
        type: componentType,
        x: 100,
        y: 100,
        ports: [
          { id: 'input', type: 'in' },
          { id: 'output', type: 'out' },
        ],
      };
      return {
        canvasComponents: [...state.canvasComponents, newComponent],
      };
    }),
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
  addLink: ({ source, target }) =>
    set((state) => {
      const linkExists = state.links.some(
        (l) =>
          l.source.componentId === source.componentId &&
          l.target.componentId === target.componentId
      );

      if (linkExists || source.componentId === target.componentId) {
        return {};
      }

      const newLink: Link = {
        id: `link_${source.componentId}_${target.componentId}`,
        source,
        target,
      };
      return { links: [...state.links, newLink] };
    }),
}));

