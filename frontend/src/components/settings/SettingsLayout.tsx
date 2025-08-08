import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../config';
import MemoryTab from './MemoryTab';
import TraceabilityTab from './TraceabilityTab';

/**
 * SettingsLayout renders the enterprise settings console with tabs for
 * different configuration areas. It fetches the current user's roles
 * and permissions from the server on mount and conditionally displays
 * tabs based on those permissions. Tabs are represented by a simple
 * button bar and the active tab's content is rendered below.
 */
interface UserProfile {
  id: string;
  org_id: string;
  roles: string[];
  permissions: string[];
}

interface TabDef {
  id: string;
  label: string;
  perm?: string;
  content: React.ReactNode;
}

const SettingsLayout: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [activeTab, setActiveTab] = useState<string>('profile');

  useEffect(() => {
    // Fetch current user information including roles/permissions
    const fetchMe = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/me`);
        if (res.ok) {
          const data = await res.json();
          setUser(data as UserProfile);
        } else {
          // Fallback to a default user with no permissions
          setUser({ id: 'anonymous', org_id: 'unknown', roles: [], permissions: [] });
        }
      } catch (err) {
        console.error('Failed to fetch user profile', err);
        setUser({ id: 'anonymous', org_id: 'unknown', roles: [], permissions: [] });
      }
    };
    fetchMe();
  }, []);

  const hasPerm = (perm?: string): boolean => {
    if (!perm) return true;
    return user?.permissions?.includes(perm) ?? false;
  };

  // Define tabs with their permission requirements and content
  const tabs: TabDef[] = [
    { id: 'profile', label: 'Profile', content: <div>Your profile settings go here.</div> },
    { id: 'organization', label: 'Organization', content: <div>Organization settings (coming soon).</div> },
    { id: 'roles', label: 'Roles & Permissions', content: <div>Role management (coming soon).</div>, perm: 'policy:edit' },
    { id: 'memory', label: 'Memory', content: <MemoryTab />, perm: 'memory:read' },
    { id: 'traceability', label: 'Traceability', content: <TraceabilityTab />, perm: 'trace:read' },
    { id: 'integrations', label: 'Integrations', content: <div>Integrations configuration (coming soon).</div>, perm: 'policy:edit' },
    { id: 'models', label: 'Models & Costs', content: <div>Model settings (coming soon).</div>, perm: 'policy:edit' },
    { id: 'automations', label: 'Automations', content: <div>Automation schedules (coming soon).</div>, perm: 'policy:edit' },
  ];

  return (
    <div className="p-4 h-full overflow-auto bg-gray-50 text-black flex flex-col">
      <h2 className="text-xl font-semibold mb-4">Settings</h2>
      <div className="flex space-x-4 border-b border-gray-200 mb-4">
        {tabs
          .filter((t) => hasPerm(t.perm))
          .map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-3 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
      </div>
      <div className="flex-1 overflow-auto">
        {tabs
          .filter((t) => hasPerm(t.perm))
          .map((tab) => (
            <div key={tab.id} className={activeTab === tab.id ? 'block' : 'hidden'}>
              {tab.content}
            </div>
          ))}
      </div>
    </div>
  );
};

export default SettingsLayout;
