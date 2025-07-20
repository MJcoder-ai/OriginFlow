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
import { DndContext, DragEndEvent } from '@dnd-kit/core';
import { useAppStore, UploadEntry } from '../appStore';
import { parseDatasheet, getFileStatus } from '../services/fileApi';

/**
 * Main layout component orchestrating structural UI elements.
 */
const Layout: React.FC = () => {
  const [isNavCollapsed, setIsNavCollapsed] = useState<boolean>(false);
  const [isActionCollapsed, setIsActionCollapsed] = useState<boolean>(false);
  const {
    addComponent,
    updateComponentPosition,
    setActiveDatasheet,
    updateUpload,
    addMessage,
  } = useAppStore();
  const componentCount = useAppStore((s) => s.canvasComponents.length);

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

    // Dropping a datasheet onto the components canvas triggers parsing
    if (over.id === 'component-canvas' && active.data.current?.type === 'file-asset') {
      const asset = active.data.current.asset as UploadEntry;
      if (asset.mime !== 'application/pdf') {
        addMessage({ id: 'err', author: 'System', text: 'Only PDF datasheets can be parsed.' });
        return;
      }
      parseDatasheet(asset.id).catch((err) => console.error(err));
      updateUpload(asset.id, { parsing_status: 'processing' });

      const poll = async () => {
        try {
          const status = await getFileStatus(asset.id);
          updateUpload(asset.id, {
            parsing_status: status.parsing_status ?? null,
            parsing_error: status.parsing_error ?? null,
            parsed_at: status.parsed_at,
          });
          if (status.parsing_status === 'success') {
            setActiveDatasheet({ id: status.id, url: status.url, payload: status.parsed_payload });
            return;
          }
          if (status.parsing_status === 'failed') {
            addMessage({ id: 'err', author: 'System', text: `Failed to parse ${asset.name}.` });
            return;
          }
          setTimeout(poll, 2000);
        } catch (e) {
          console.error(e);
        }
      };
      poll();
      return;
    }

    // Otherwise reposition existing component
    if (active.data.current?.type !== 'file-asset') {
      updateComponentPosition(active.id as string, delta);
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
        <StatusBar />
      </div>
    </DndContext>
  );
};

export default Layout;
