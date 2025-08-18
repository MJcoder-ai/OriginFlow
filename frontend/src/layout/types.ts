export type GraphNode = {
  id: string;
  width?: number;
  height?: number;
  layout?: Record<string, { x: number; y: number }>;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
};
