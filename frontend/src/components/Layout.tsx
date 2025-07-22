/**
 * File: frontend/src/components/Layout.tsx
 * Provides the application layout using CSS Grid with collapsible sidebar
 * and action bar sections for responsive engineer UI.
 */
import React, { useContext } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import ActionBar from './ActionBar';
import MainPanel from './MainPanel';
import StatusBar from './StatusBar';
import ChatSidebar from './ChatSidebar';
import { DndContext, DragEndEvent } from '@dnd-kit/core';
import { useAppStore, UploadEntry } from '../appStore';
import { UIContext } from '../context/UIContext';

/**
 * Main layout component orchestrating structural UI elements.
 */
const Layout: React.FC = () => {
  const { addComponent, updateComponentPosition } = useAppStore();
  const { isSidebarCollapsed, isSubNavVisible } = useContext(UIContext);

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

  const sidebarWidth = isSidebarCollapsed ? '64px' : '250px';

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div
        className="h-screen w-screen grid"
        style={{
          gridTemplateColumns: `${sidebarWidth} 1fr 350px`,
          gridTemplateRows: `${isSubNavVisible ? 'auto auto' : 'auto'} 1fr`,
          gridTemplateAreas: `\n            "header header header"\n            ${isSubNavVisible ? '"toolbar toolbar toolbar"' : ''}\n            "sidebar main chat"\n          `,
        }}
      >
        <div style={{ gridArea: 'header' }}>
          <Header />
        </div>
        {isSubNavVisible && (
          <div style={{ gridArea: 'toolbar' }}>
            <ActionBar />
          </div>
        )}
        <div style={{ gridArea: 'sidebar' }}>
          <Sidebar />
        </div>
        <div style={{ gridArea: 'main', overflow: 'hidden' }}>
          <MainPanel />
        </div>
        <div style={{ gridArea: 'chat' }}>
          <ChatSidebar />
        </div>
      </div>
      <div className="fixed bottom-0 w-full z-50">
        <StatusBar />
      </div>
    </DndContext>
  );
};

export default Layout;
