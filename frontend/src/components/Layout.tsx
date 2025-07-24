import React, { useState } from 'react';
import Header from './Header';
import Toolbar from './Toolbar';
import Sidebar from './Sidebar';
import ProjectCanvas from './ProjectCanvas';
import ComponentCanvas from './ComponentCanvas';
import ChatSidebar from './ChatSidebar';
import StatusBar from './StatusBar';
import { ChatInput } from './ChatInput';
import { useAppStore } from '../appStore';

const Layout: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSubNavVisible, setIsSubNavVisible] = useState(true);
  const route = useAppStore((s) => s.route);

  return (
    <div className="h-screen flex flex-col">
      <div
        className="grid h-full w-full transition-all duration-300 ease-in-out"
        style={{
          gridTemplateColumns: `${isSidebarCollapsed ? '64px' : '250px'} 1fr 350px`,
          // Use auto sizing for the last row so the chat input can expand beyond 48px.
          gridTemplateRows: '64px 48px 1fr auto',
          gridTemplateAreas: `
            "header header header"
            "toolbar toolbar toolbar"
            "sidebar main chat"
            "status status chatInput"
          `,
        }}
      >
        {/* Header wrapper ensures grid area is applied to the correct element */}
        <div className="grid-in-header">
          <Header
            toggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            toggleToolbar={() => setIsSubNavVisible(!isSubNavVisible)}
          />
        </div>

        {isSubNavVisible && (
          <div className="grid-in-toolbar">
            <Toolbar />
          </div>
        )}

        <div
          className="grid-in-sidebar transition-all duration-300 ease-in-out"
          aria-label="Main navigation"
        >
          <Sidebar isCollapsed={isSidebarCollapsed} />
        </div>

        <div className="grid-in-main overflow-hidden">
          {route === 'components' ? <ComponentCanvas /> : <ProjectCanvas />}
        </div>

        {/* Chat sidebar: placed in the grid. Responsive visibility can be controlled via CSS classes in ChatSidebar */}
        <div className="grid-in-chat">
          <ChatSidebar />
        </div>

        {/* Status bar wrapper avoids nested <footer> elements */}
        <div className="grid-in-status">
          <StatusBar />
        </div>

        <div className="grid-in-chatInput">
          <ChatInput />
        </div>
      </div>
    </div>
  );
};

export default Layout;
