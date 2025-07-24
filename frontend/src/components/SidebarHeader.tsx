interface Props {
  isCollapsed: boolean;
}

const SidebarHeader = ({ isCollapsed }: Props) => (
  <div
    className={`grid-in-sidebar-header flex items-center p-4 h-16 border-b border-r border-gray-200 ${
      isCollapsed ? 'justify-center' : 'justify-start'
    }`}
  >
    <a href="/" className="flex items-center gap-2">
      <span className="text-2xl">🌀</span>
      {!isCollapsed && <h1 className="text-xl font-bold">OriginFlow</h1>}
    </a>
  </div>
);

export default SidebarHeader;
