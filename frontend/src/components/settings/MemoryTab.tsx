import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '../../config';
import { Memory } from '../../types/memory';

/**
 * MemoryTab lists memory entries returned from the backend. It
 * performs a simple fetch on mount and renders a table with a few
 * important fields. Pagination and filters can be added later.
 */
const MemoryTab: React.FC = () => {
  const [items, setItems] = useState<Memory[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/memory`);
        if (res.ok) {
          const data = await res.json();
          setItems(data as Memory[]);
        } else {
          setError(`Failed to load memory: ${res.status}`);
        }
      } catch (err: any) {
        setError(`Failed to load memory: ${err.message ?? err}`);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Memory Entries</h3>
      {error && <div className="text-red-600 text-sm">{error}</div>}
      <div className="overflow-x-auto">
        <table className="min-w-full border text-xs text-left">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-3 py-2 font-medium">ID</th>
              <th className="px-3 py-2 font-medium">Kind</th>
              <th className="px-3 py-2 font-medium">Project</th>
              <th className="px-3 py-2 font-medium">Created</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t">
                <td className="px-3 py-1 font-mono">{item.id}</td>
                <td className="px-3 py-1">{item.kind}</td>
                <td className="px-3 py-1">{item.project_id ?? '-'}</td>
                <td className="px-3 py-1">
                  {new Date(item.created_at).toLocaleString(undefined, {
                    dateStyle: 'short',
                    timeStyle: 'short',
                  })}
                </td>
              </tr>
            ))}
            {items.length === 0 && !error && (
              <tr>
                <td colSpan={4} className="px-3 py-4 text-center text-gray-500">
                  No memory entries found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MemoryTab;
