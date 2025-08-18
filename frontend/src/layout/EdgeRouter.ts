import type { GraphNode, GraphEdge } from "./types";
import { LayerName } from "./LayoutManager";

type Points = { x: number; y: number }[];
export type EdgePaths = Record<string, Points>;

let elkPromise: Promise<any> | null = null;
async function getElk() {
  if (!elkPromise) elkPromise = import("elkjs");
  return elkPromise;
}

// Client-side elkjs orthogonal routing
export async function routeEdgesElk(
  nodes: GraphNode[],
  edges: GraphEdge[],
  layer: LayerName,
  lockedLinks: Record<string, boolean>,
): Promise<EdgePaths> {
  const { default: ELK } = await getElk();
  const elk = new ELK();
  const graph: any = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.edgeRouting": "ORTHOGONAL",
    },
    children: nodes.map((n) => ({
      id: n.id,
      x: n.layout?.[layer]?.x ?? 0,
      y: n.layout?.[layer]?.y ?? 0,
      width: n.width ?? 120,
      height: n.height ?? 72,
      properties: { "org.eclipse.elk.fixed": true },
    })),
    edges: edges.map((e) => ({ id: e.id, sources: [e.source], targets: [e.target] })),
  };
  const out = await elk.layout(graph);
  const paths: EdgePaths = {};
  for (const e of out.edges ?? []) {
    if (lockedLinks[e.id]) continue;
    const sections = e.sections ?? [];
    const pts: Points = [];
    for (const s of sections) {
      if (s.startPoint)
        pts.push({ x: Math.round(s.startPoint.x), y: Math.round(s.startPoint.y) });
      for (const b of s.bendPoints ?? [])
        pts.push({ x: Math.round(b.x), y: Math.round(b.y) });
      if (s.endPoint)
        pts.push({ x: Math.round(s.endPoint.x), y: Math.round(s.endPoint.y) });
    }
    if (pts.length) paths[e.id] = pts;
  }
  return paths;
}

