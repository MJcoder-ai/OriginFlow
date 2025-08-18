// LayoutManager: picks elkjs (preferred) or dagre (fallback) to compute positions for UNLOCKED nodes.
// After computing, the caller is expected to PATCH the updated coordinates back to the server.

import type { GraphNode, GraphEdge } from "./types";

export type LayerName = "single_line" | "high_level" | "civil" | "networking" | "physical";

type Positions = Record<string, { x: number; y: number }>;

let elkPromise: Promise<any> | null = null;
let dagrePromise: Promise<any> | null = null;

async function getElk() {
  if (!elkPromise) elkPromise = import("elkjs");
  return elkPromise;
}

async function getDagre() {
  if (!dagrePromise) dagrePromise = import("dagre");
  return dagrePromise;
}

export async function layoutWithElk(
  nodes: GraphNode[],
  edges: GraphEdge[],
  layer: LayerName,
  locked: Set<string>
): Promise<Positions> {
  const { default: ELK } = await getElk();
  const elk = new ELK();
  const graph = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.spacing.nodeNode": "50",
      "elk.layered.spacing.nodeNodeBetweenLayers": "120",
    },
    children: nodes.map((n) => {
      const base: any = {
        id: n.id,
        width: n.width ?? 120,
        height: n.height ?? 72,
      };
      if (locked.has(n.id) && n.layout?.[layer]) {
        base.x = n.layout[layer].x;
        base.y = n.layout[layer].y;
        base.properties = { "org.eclipse.elk.fixed": true };
      }
      return base;
    }),
    edges: edges.map((e) => ({ id: e.id, sources: [e.source], targets: [e.target] })),
  };
  const res = await elk.layout(graph);
  const out: Positions = {};
  for (const c of res.children ?? []) {
    if (!locked.has(c.id)) {
      out[c.id] = { x: Math.round(c.x), y: Math.round(c.y) };
    }
  }
  return out;
}

export async function layoutWithDagre(
  nodes: GraphNode[],
  edges: GraphEdge[],
  layer: LayerName,
  locked: Set<string>
): Promise<Positions> {
  const dagre = await getDagre();
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: "LR", nodesep: 50, ranksep: 120 });
  g.setDefaultEdgeLabel(() => ({}));

  nodes.forEach((n) => {
    g.setNode(n.id, { width: n.width ?? 120, height: n.height ?? 72 });
  });
  edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);

  const out: Positions = {};
  nodes.forEach((n) => {
    if (!locked.has(n.id)) {
      const pos = g.node(n.id);
      if (pos) out[n.id] = { x: Math.round(pos.x), y: Math.round(pos.y) };
    }
  });
  return out;
}

export async function suggestLayout(
  nodes: GraphNode[],
  edges: GraphEdge[],
  layer: LayerName,
  lockedInLayer: Record<string, boolean>
): Promise<Positions> {
  const locked = new Set<string>(Object.keys(lockedInLayer).filter((id) => lockedInLayer[id]));
  try {
    return await layoutWithElk(nodes, edges, layer, locked);
  } catch {
    return await layoutWithDagre(nodes, edges, layer, locked);
  }
}
