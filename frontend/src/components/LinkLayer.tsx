/**
 * File: frontend/src/components/LinkLayer.tsx
 * Renders SVG lines for all connections between components.
 * Computes line positions from DOM element centers and observes state changes.
 */
import React, { useLayoutEffect, useState } from 'react';
import { useAppStore } from '../appStore';

/**
 * Determine the center coordinates of a component card DOM element.
 */
const getComponentCenter = (id: string): { x: number; y: number } | null => {
  const element = document.getElementById(id);
  if (!element) return null;
  const rect = element.getBoundingClientRect();
  const parentRect = element.parentElement?.getBoundingClientRect();
  if (!parentRect) return null;
  return {
    x: rect.left - parentRect.left + rect.width / 2,
    y: rect.top - parentRect.top + rect.height / 2,
  };
};

/** Overlay drawing lines between linked components. */
const LinkLayer: React.FC = () => {
  const links = useAppStore((state) => state.links);
  const components = useAppStore((state) => state.canvasComponents);
  // Force a re-render after layout to pick up element positions
  const [, setRender] = useState<number>(0);

  useLayoutEffect(() => {
    setRender((r) => r + 1);
  }, [links, components]);

  const renderedLinks = links
    .map((link) => {
      const sourcePos = getComponentCenter(`component-card-${link.sourceId}`);
      const targetPos = getComponentCenter(`component-card-${link.targetId}`);
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

  return (
    <svg className="absolute top-0 left-0 w-full h-full pointer-events-none">
      {renderedLinks as React.ReactNode[]}
    </svg>
  );
};

export default LinkLayer;
