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
        className="grid h-full w-full transition-all duration-300 ease-in-out grid-areas-layout"
        style={{
          gridTemplateColumns: `${isSidebarCollapsed ? '64px' : '250px'} 1fr 350px`,
          gridTemplateRows: '64px 48px 1fr 48px',
        }}
      >
        <header className="grid-in-header">
          <Header
            toggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            toggleToolbar={() => setIsSubNavVisible(!isSubNavVisible)}
          />
        </header>

        {isSubNavVisible && (
          <div className="grid-in-toolbar">
            <Toolbar />
          </div>
        )}

        <aside
          className={`grid-in-sidebar transition-all duration-300 ease-in-out ${
            isSidebarCollapsed ? 'w-16' : 'w-64'
          }`}
          aria-label="Main navigation"
        >
          <Sidebar isCollapsed={isSidebarCollapsed} />
        </aside>

        <main className="grid-in-main overflow-hidden">
          {route === 'components' ? <ComponentCanvas /> : <ProjectCanvas />}
        </main>

        <div className="grid-in-chat fixed right-0 top-0 h-full z-50 shadow-2xl xl:static xl:shadow-none">
          <ChatSidebar />
        </div>

        <footer className="grid-in-status">
          <StatusBar />
        </footer>

        <div className="grid-in-chatInput">
          <ChatInput />
        </div>
      </div>
    </div>
  );
};

export default Layout;
