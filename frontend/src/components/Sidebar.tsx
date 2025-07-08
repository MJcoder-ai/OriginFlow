/**
 * File: frontend/src/components/Sidebar.tsx
 * Collapsible sidebar navigation used across the engineer UI.
 * Renders the application logo and navigation items with icons.
 */
import React from 'react';
import {
    LayoutDashboard,
    FolderKanban,
    Box,
    FileText,
    ListTodo,
    Bot,
    Users,
    Settings,
    LifeBuoy,
} from 'lucide-react';
import clsx from 'clsx';

// Data for the navigation items
const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard' },
    { icon: FolderKanban, label: 'Projects' },
    { icon: Box, label: 'Components' },
    { icon: FileText, label: 'Files' },
    { icon: ListTodo, label: 'Tasks' },
    { icon: Bot, label: 'AI Assistant' },
    { icon: Users, label: 'Team' },
    { icon: Settings, label: 'Settings' },
];

interface SidebarProps {
  /** Whether the sidebar is collapsed. */
  isCollapsed: boolean;
}

const NavItem: React.FC<{ item: typeof navItems[0]; isCollapsed: boolean; isActive?: boolean }> = ({ item, isCollapsed, isActive }) => {
    const Icon = item.icon;
    return (
        <a href="#" className={clsx('flex items-center p-2 rounded-lg text-gray-600 hover:bg-gray-100 hover:text-gray-900', { 'bg-gray-100 font-semibold text-gray-900': isActive })}>
            <Icon size={20} className="flex-shrink-0" />
            <span className={clsx('ml-3 transition-opacity duration-200', { 'opacity-0': isCollapsed, 'opacity-100': !isCollapsed })}>{item.label}</span>
        </a>
    );
};

/** Sidebar navigation drawer. */
const Sidebar: React.FC<SidebarProps> = ({ isCollapsed }) => {
  return (
    <aside className="[grid-area:sidebar] bg-white border-r border-gray-200 p-4 flex flex-col">
      <div className="h-14 flex items-center justify-center mb-4">
        <div className="h-10 w-32 bg-gray-100 rounded-md flex items-center justify-center font-bold">Logo_1</div>
      </div>
      <nav className="flex-grow space-y-1">
        {navItems.map((item) => (
          <NavItem key={item.label} item={item} isCollapsed={isCollapsed} isActive={item.label === 'Files'} />
        ))}
      </nav>
      <div className="flex-shrink-0">
        <NavItem item={{ icon: LifeBuoy, label: 'Help & Support' }} isCollapsed={isCollapsed} />
      </div>
    </aside>
  );
};

export default Sidebar;
