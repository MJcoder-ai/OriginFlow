/**
 * File: frontend/src/components/Layout.tsx
 * Provides the application layout using CSS Grid with collapsible sidebar
 * and action bar sections for responsive engineer UI.
 */
import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import ActionBar from './ActionBar';
import MainPanel from './MainPanel';
import { FileStagingArea } from './FileStagingArea';
import StatusBar from './StatusBar';
import { DndContext, DragEndEvent } from '@dnd-kit/core';
import { useAppStore } from '../appStore';
import { PALETTE_COMPONENT_DRAG_TYPE } from './ComponentPalette';

/**
 * Main layout component orchestrating structural UI elements.
 */
const Layout: React.FC = () => {
  const [isNavCollapsed, setIsNavCollapsed] = useState<boolean>(false);
  const [isActionCollapsed, setIsActionCollapsed] = useState<boolean>(false);
  const { addComponent, updateComponentPosition } = useAppStore();
  const componentCount = useAppStore((s) => s.canvasComponents.length);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over, delta } = event;
    if (active.id && over) {
      if (
        over.id === 'canvas-area' &&
        active.data.current?.type === PALETTE_COMPONENT_DRAG_TYPE
      ) {
        const ctype = active.data.current?.componentType;
        if (ctype) {
          addComponent({
            name: `${ctype} ${componentCount + 1}`,
            type: ctype,
            standard_code: `CODE-${Date.now()}`,
            x: 100,
            y: 100,
          });
        }
      } else if (
        over.id === 'canvas-area' &&
        active.data.current?.type === 'file-asset'
      ) {
        const asset = active.data.current?.asset;
        if (asset) {
          addComponent({
            name: asset.name,
            type: 'Datasheet',
            standard_code: `CODE-${Date.now()}`,
            x: 100,
            y: 100,
          });
        }
      } else if (active.data.current?.type !== PALETTE_COMPONENT_DRAG_TYPE) {
        updateComponentPosition(active.id as string, delta);
      }
    }
  };

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div
        className={`grid h-screen transition-all duration-200 \
        ${isNavCollapsed ? 'grid-cols-[80px_1fr]' : 'grid-cols-[240px_1fr]'} \
        ${isActionCollapsed ? 'grid-rows-[60px_0_1fr_40px]' : 'grid-rows-[60px_48px_1fr_40px]'}
        grid-areas-layout-desktop`}
      >
        <Sidebar isCollapsed={isNavCollapsed} />
        <Header
          isNavCollapsed={isNavCollapsed}
          toggleNavCollapse={() => setIsNavCollapsed(!isNavCollapsed)}
          toggleActionCollapse={() => setIsActionCollapsed(!isActionCollapsed)}
        />
        <ActionBar isCollapsed={isActionCollapsed} />
        <MainPanel />
        <FileStagingArea />
        <StatusBar />
      </div>
    </DndContext>
  );
};

export default Layout;
