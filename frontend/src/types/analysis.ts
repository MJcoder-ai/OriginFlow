export interface CanvasComponentSnap {
  id: string;
  name: string;
  type: string;
  standard_code: string;
  x: number;
  y: number;
}

export interface CanvasLinkSnap {
  id: string;
  source_id: string;
  target_id: string;
  path_by_layer?: Record<string, { x: number; y: number }[]>;
  locked_in_layers?: Record<string, boolean>;
}

export interface DesignSnapshot {
  components: CanvasComponentSnap[];
  links: CanvasLinkSnap[];
}
