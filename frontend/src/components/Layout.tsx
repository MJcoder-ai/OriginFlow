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
import StatusBar from './StatusBar';
import ChatSidebar from './ChatSidebar';
import { DndContext, DragEndEvent } from '@dnd-kit/core';
import { useAppStore, UploadEntry } from '../appStore';

/**
 * Main layout component orchestrating structural UI elements.
 */
const Layout: React.FC = () => {
  const [isNavCollapsed, setIsNavCollapsed] = useState<boolean>(false);
  const [isActionCollapsed, setIsActionCollapsed] = useState<boolean>(false);
  const { addComponent, updateComponentPosition } = useAppStore();

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over, delta } = event;
    if (!active.id || !over) return;

    // Dropping a component asset onto the project canvas adds an instance
    if (over.id === 'canvas-area' && active.data.current?.type === 'file-asset') {
      const asset = active.data.current.asset as UploadEntry;
      addComponent({
        name: asset.name,
        type: 'Datasheet',
        standard_code: `CODE-${Date.now()}`,
        x: 100,
        y: 100,
      });
      return;
    }

    // Dropping a datasheet onto the components canvas is handled locally

    // Otherwise reposition existing component
    if (active.data.current?.type !== 'file-asset') {
      updateComponentPosition(active.id as string, delta);
    }
  };

  const gridCols = isNavCollapsed ? 'grid-cols-[60px_1fr_350px]' : 'grid-cols-[180px_1fr_350px]';

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div
        className={`grid h-screen w-screen grid-rows-[48px_48px_1fr_40px] ${gridCols} grid-areas-layout`}
      >
        <Header
          isNavCollapsed={isNavCollapsed}
          toggleNavCollapse={() => setIsNavCollapsed(!isNavCollapsed)}
          toggleActionCollapse={() => setIsActionCollapsed(!isActionCollapsed)}
        />
        <ActionBar isCollapsed={isActionCollapsed} />
        <Sidebar isCollapsed={isNavCollapsed} />
        <MainPanel />
        <ChatSidebar className="[grid-area:chat]" />
        <StatusBar />
      </div>
    </DndContext>
  );
};

export default Layout;
