/**
 * File: frontend/src/appStore.ts
 * Central Zustand store for application state management.
 * Tracks canvas components, links, and current selection.
 * Exposed via the `useAppStore` hook for React components.
 */
import { create } from 'zustand';

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
}

/**
 * Representation of a connection between two canvas components.
 */
export interface Link {
  /** Unique identifier for this link. */
  id: string;
  /** Source component identifier. */
  sourceId: string;
  /** Target component identifier. */
  targetId: string;
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
  addLink: (link: { sourceId: string; targetId: string }) => void;
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
  addLink: ({ sourceId, targetId }) =>
    set((state) => {
      const linkExists = state.links.some(
        (l) =>
          (l.sourceId === sourceId && l.targetId === targetId) ||
          (l.sourceId === targetId && l.targetId === sourceId)
      );

      if (linkExists || sourceId === targetId) {
        return {};
      }

      const newLink: Link = {
        id: `link_${sourceId}_${targetId}`,
        sourceId,
        targetId,
      };
      return { links: [...state.links, newLink] };
    }),
}));

