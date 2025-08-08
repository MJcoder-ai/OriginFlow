import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '../../config';
import { TraceSummary, TraceEvent } from '../../types/trace';

/**
 * TraceabilityTab displays a list of traces and, when one is selected,
 * renders the events within that trace. This initial implementation
 * keeps the UI simple: a master list on the left and the detail view
 * on the right. Future enhancements could include pagination,
 * filtering and export capabilities.
 */
const TraceabilityTab: React.FC = () => {
  const [traces, setTraces] = useState<TraceSummary[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTraces = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/traces`);
        if (!res.ok) {
          setError(`Failed to load traces: ${res.status}`);
          return;
        }
        const data = await res.json();
        setTraces(data as TraceSummary[]);
      } catch (err: any) {
        setError(`Failed to load traces: ${err.message ?? err}`);
      }
    };
    loadTraces();
  }, []);

  useEffect(() => {
    if (!selected) {
      setEvents([]);
      return;
    }
    const loadEvents = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/traces/${selected}`);
        if (!res.ok) {
          setError(`Failed to load events: ${res.status}`);
          return;
        }
        const data = await res.json();
        setEvents(data as TraceEvent[]);
      } catch (err: any) {
        setError(`Failed to load events: ${err.message ?? err}`);
      }
    };
    loadEvents();
  }, [selected]);

  return (
    <div className="space-y-4 h-full flex flex-col">
      <h3 className="text-lg font-semibold">Traceability</h3>
      {error && <div className="text-red-600 text-sm">{error}</div>}
      <div className="flex-1 flex overflow-hidden">
        <div className="w-1/3 pr-2 border-r overflow-y-auto">
          <h4 className="font-medium mb-2">Traces</h4>
          <ul className="divide-y">
            {traces.map((trace) => (
              <li
                key={trace.trace_id}
                className={`p-2 cursor-pointer ${
                  selected === trace.trace_id ? 'bg-blue-50' : 'hover:bg-gray-100'
                }`}
                onClick={() => setSelected(trace.trace_id)}
              >
                <div className="font-mono text-xs truncate">{trace.trace_id}</div>
                <div className="text-xs text-gray-500">
                  {trace.count} event{trace.count === 1 ? '' : 's'}
                </div>
              </li>
            ))}
            {traces.length === 0 && (
              <li className="p-2 text-gray-500 text-sm">No traces found.</li>
            )}
          </ul>
        </div>
        <div className="w-2/3 pl-2 overflow-y-auto">
          <h4 className="font-medium mb-2">Events</h4>
          {selected && events.length === 0 && (
            <div className="text-sm text-gray-500">No events for this trace.</div>
          )}
          {events.map((e) => (
            <div key={e.id} className="border-b pb-2 mb-2">
              <div className="text-xs font-semibold">
                {new Date(e.ts).toLocaleString(undefined, {
                  dateStyle: 'short',
                  timeStyle: 'short',
                })}
                &nbsp;-&nbsp;
                {e.event_type}
              </div>
              <pre className="whitespace-pre-wrap bg-gray-50 p-2 rounded text-xs overflow-x-auto">
                {JSON.stringify(e.payload, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TraceabilityTab;
