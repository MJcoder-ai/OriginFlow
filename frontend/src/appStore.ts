/**
 * File: frontend/src/appStore.ts
 * Defines a small Zustand store for global UI state.
 * Manages canvas components and the user selection logic.
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
}

/**
 * Shape of the global application state managed by Zustand.
 */
interface AppState {
  /** Components currently placed on the canvas. */
  canvasComponents: CanvasComponent[];
  /** The id of the currently selected component. */
  selectedComponentId: string | null;
  /** Update which component is selected. */
  selectComponent: (id: string | null) => void;
  /** Add a component to the canvas using its type. */
  addComponent: (componentType: string) => void;
}

/**
 * Create a Zustand store with basic component management helpers.
 */
export const useAppStore = create<AppState>((set) => ({
  canvasComponents: [],
  selectedComponentId: null,
  selectComponent: (id) => set({ selectedComponentId: id }),
  addComponent: (componentType) =>
    set((state) => {
      const newComponent: CanvasComponent = {
        id: `component_${Date.now()}`,
        name: `${componentType} ${state.canvasComponents.length + 1}`,
        type: componentType,
      };
      return {
        canvasComponents: [...state.canvasComponents, newComponent],
      };
    }),
}));

