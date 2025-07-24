import { useState } from 'react';
import Header from './Header';
import MainPanel from './MainPanel';
import Sidebar from './Sidebar';
import SidebarHeader from './SidebarHeader';
import SidebarFooter from './SidebarFooter';
import StatusBar from './StatusBar';
import Toolbar from './Toolbar';
import ChatHistory from './ChatHistory';
import ChatInputArea from './ChatInputArea';
import ChatFooter from './ChatFooter';
const Layout = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSubNavVisible, setIsSubNavVisible] = useState(true);

  return (
    <div
      className="grid h-screen w-screen min-h-0 transition-all duration-300 ease-in-out"
      style={{
        gridTemplateColumns: `${isSidebarCollapsed ? '64px' : '250px'} 1fr 350px`,
        gridTemplateRows: '64px 48px 1fr auto auto',
        gridTemplateAreas: `
          "sidebar-header header      chat-history"
          "sidebar        toolbar     chat-history"
          "sidebar        main        chat-history"
          "sidebar        main        chat-input"
          "sidebar-footer status      chat-footer"
        `,
      }}
    >
      <SidebarHeader isCollapsed={isSidebarCollapsed} />
      <Header
        toggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        toggleToolbar={() => setIsSubNavVisible(!isSubNavVisible)}
      />
      {isSubNavVisible && <Toolbar />}
      <Sidebar isCollapsed={isSidebarCollapsed} />
      <div className="grid-in-main relative min-h-0 overflow-auto bg-gray-50">
        <MainPanel />
      </div>
      <ChatHistory />
      <ChatInputArea />
      <ChatFooter />
      <SidebarFooter isCollapsed={isSidebarCollapsed} />
      <StatusBar />
    </div>
  );
};

export default Layout;
