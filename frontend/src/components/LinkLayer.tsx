/**
 * File: frontend/src/components/LinkLayer.tsx
 * Renders SVG lines for all connections and the pending link.
 * Computes line positions from DOM element centers and observes state changes.
 * Shows a temporary "rubber band" line while the user is connecting ports.
*/
import React, { useLayoutEffect, useState } from 'react';
import { useAppStore } from '../appStore';

/**
 * Determine the center coordinates of a component card DOM element.
 */
const getPortPosition = (
  componentId: string,
  portId: string
): { x: number; y: number } | null => {
  const portElement = document.getElementById(`port_${componentId}_${portId}`);
  if (!portElement) return null;
  const canvasArea = portElement.closest('.canvas-area-container');
  if (!canvasArea) return null;
  const canvasRect = canvasArea.getBoundingClientRect();
  const portRect = portElement.getBoundingClientRect();
  return {
    x: portRect.left - canvasRect.left + portRect.width / 2,
    y: portRect.top - canvasRect.top + portRect.height / 2,
  };
};

/** Props for the {@link LinkLayer} component. */
interface LinkLayerProps {
  /** Information on the link currently being drawn. */
  pendingLink: { sourceId: string; portId: 'output' } | null;
  /** Current mouse coordinates within the canvas. */
  mousePos: { x: number; y: number };
}

/** Overlay drawing lines between linked components. */
const LinkLayer: React.FC<LinkLayerProps> = ({ pendingLink, mousePos }) => {
  const links = useAppStore((state) => state.links);
  const components = useAppStore((state) => state.canvasComponents);
  // Force a re-render after layout to pick up element positions
  const [, setRender] = useState<number>(0);

  useLayoutEffect(() => {
    setRender((r) => r + 1);
  }, [links, components]);

  const renderedLinks = links
    .map((link) => {
      const sourcePos = getPortPosition(link.source_id, 'output');
      const targetPos = getPortPosition(link.target_id, 'input');
      if (!sourcePos || !targetPos) {
        return null;
      }
      return (
        <line
          key={link.id}
          x1={sourcePos.x}
          y1={sourcePos.y}
          x2={targetPos.x}
          y2={targetPos.y}
          className="stroke-gray-500 stroke-2"
        />
      );
    })
    .filter(Boolean);

  let pendingLinkLine: React.ReactNode = null;
  if (pendingLink) {
    const sourcePos = getPortPosition(pendingLink.sourceId, pendingLink.portId);
    if (sourcePos) {
      pendingLinkLine = (
        <line
          x1={sourcePos.x}
          y1={sourcePos.y}
          x2={mousePos.x}
          y2={mousePos.y}
          className="stroke-blue-500 stroke-2 stroke-dasharray-4"
        />
      );
    }
  }

  return (
    <svg className="absolute top-0 left-0 w-full h-full pointer-events-none">
      {renderedLinks as React.ReactNode[]}
      {pendingLinkLine}
    </svg>
  );
};

export default LinkLayer;
