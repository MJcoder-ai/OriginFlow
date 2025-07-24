import { LifeBuoy } from 'lucide-react';

interface Props {
  isCollapsed: boolean;
}

const SidebarFooter = ({ isCollapsed }: Props) => (
  <div className="grid-in-sidebar-footer p-2 border-t border-r border-gray-200 bg-white">
    <a
      href="#"
      className="flex items-center gap-3 px-4 py-2 text-sm font-medium rounded-md hover:bg-gray-100"
    >
      <LifeBuoy size={20} />
      {!isCollapsed && <span>Help & Support</span>}
    </a>
  </div>
);

export default SidebarFooter;
