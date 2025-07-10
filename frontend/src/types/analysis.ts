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
}

export interface DesignSnapshot {
  components: CanvasComponentSnap[];
  links: CanvasLinkSnap[];
}
