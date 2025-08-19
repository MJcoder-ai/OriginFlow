import React from 'react';
import Workspace from './Workspace';
import ComponentCanvas from './ComponentCanvas';
// Import the enterprise settings console. The existing SettingsPanel
// component remains in the codebase but is superseded by the more
// comprehensive SettingsLayout which lives in the settings folder.
import SettingsLayout from './settings/SettingsLayout';
import { useAppStore } from '../appStore';
import AgentsPanel from './agents/AgentsPanel';
import ApprovalsPanel from './ApprovalsPanel';

const MainPanel: React.FC = () => {
  const route = useAppStore((s) => s.route);
  return (
    <main className="grid-in-main flex flex-col bg-gray-50 text-black h-full w-full p-2 overflow-hidden">
      {route === 'projects' && <Workspace />}
      {route === 'components' && (
        /* Always render the ComponentCanvas so the droppable area is available. */
        <ComponentCanvas />
      )}
      {route === 'settings' && <SettingsLayout />}
      {route === 'agents' && <AgentsPanel />}
      {route === 'approvals' && <ApprovalsPanel />}
    </main>
  );
};

export default MainPanel;
