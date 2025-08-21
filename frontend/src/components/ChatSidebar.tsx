import React, { useEffect, useMemo, useState } from 'react';
import { useAppStore } from '../appStore';
import PlanTimeline from './PlanTimeline';
import ChatHistory from './ChatHistory';
import ChatInputArea from './ChatInputArea';
import { api } from '../services/api';

const Divider: React.FC = () => (
  <div className="h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent" />
);

/**
 * Innovative, iterative ChatSidebar that visualizes the plan timeline,
 * streaming agent cards, and provides an auto-iterate mode to drive the
 * design to completion.
 */
const ChatSidebar: React.FC = () => {
  const sessionId = useAppStore((s) => s.sessionId);
  const planTasks = useAppStore((s) => s.planTasks);
  const setPlanTasks = useAppStore((s) => s.setPlanTasks);
  const addStatusMessage = useAppStore((s) => s.addStatusMessage);
  const addMessage = useAppStore((s) => s.addMessage);
  const graphVersion = useAppStore((s) => s.graphVersion);
  const setGraphVersion = useAppStore((s) => s.setGraphVersion);
  const currentLayer = useAppStore((s) => s.currentLayer);

  const [autoIterate, setAutoIterate] = useState<boolean>(false);
  const [minConfidence, setMinConfidence] = useState<number>(0.6);
  const nextPending = useMemo(() => planTasks.find((t) => t.status === 'pending'), [planTasks]);

  // Auto-iterate: when toggled on, run the next pending task until blocked/low-confidence
  useEffect(() => {
    if (!autoIterate || !sessionId) return;
    let cancelled = false;
    (async () => {
      try {
        // Find next pending task
        const current = planTasks.find((t) => t.status === 'pending');
        if (!current) return;
        addStatusMessage(`Running ${current.title}…`, 'info');
        const res = await api.act(sessionId, current.id, undefined, graphVersion);
        if (cancelled) return;
        if (typeof res.version === 'number') setGraphVersion(res.version);
        if (res.card) {
          addMessage({ id: crypto.randomUUID(), author: 'AI', text: res.card.title, card: {
            title: res.card.title,
            description: res.card.body,
            specs: res.card.specs?.map((s: any) => ({ label: s.label, value: s.value })),
            actions: res.card.actions?.map((a: any) => ({ label: a.label, command: a.command })),
            confidence: res.card.confidence,
          }, type: 'card' });
        }
        // Update tasks if provided by backend
        if (Array.isArray(res.updated_tasks)) {
          setPlanTasks(res.updated_tasks.map((t: any) => ({
            id: t.id,
            title: t.title,
            description: t.reason || t.description,
            status: t.status,
          })));
        } else {
          // Fallback: refresh plan
          try {
            const plan = await api.getPlanForSession(sessionId, 'design system', currentLayer);
            if (Array.isArray(plan.tasks)) setPlanTasks(plan.tasks as any);
          } catch {}
        }
        // Continue only if not blocked and next task meets confidence
        const nextId = res.next_recommended_task;
        const confidence = (res.card?.confidence as number | undefined) ?? 1.0;
        if (res.status !== 'blocked' && nextId && confidence >= minConfidence) {
          // loop by updating state which retriggers effect
          addStatusMessage(`Continuing with ${nextId}…`, 'info');
        } else {
          setAutoIterate(false);
        }
      } catch (e: any) {
        setAutoIterate(false);
        addStatusMessage('Auto-iterate stopped due to error', 'error');
        console.error(e);
      }
    })();
    return () => { cancelled = true; };
  }, [autoIterate, planTasks, sessionId, graphVersion, minConfidence]);

  return (
    <aside className="grid-in-chat flex flex-col h-full border-l border-gray-200 bg-white">
      {/* Header controls */}
      <div className="px-4 py-3 flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-gray-900">Design Assistant</div>
          <div className="text-xs text-gray-500">Plan–Act loop with dynamic tasks</div>
        </div>
        <div className="flex items-center space-x-3">
          <label className="flex items-center space-x-2 text-xs text-gray-700">
            <input
              type="checkbox"
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              checked={autoIterate}
              onChange={(e) => setAutoIterate(e.target.checked)}
            />
            <span>Auto-iterate</span>
          </label>
          <div className="flex items-center space-x-1 text-xs text-gray-700">
            <span>Min confidence</span>
            <input
              type="number"
              step="0.05"
              min={0}
              max={1}
              value={minConfidence}
              onChange={(e) => setMinConfidence(Math.min(1, Math.max(0, parseFloat(e.target.value) || 0)))}
              className="w-14 px-2 py-1 border rounded"
            />
          </div>
        </div>
      </div>
      <Divider />

      {/* Plan timeline */}
      <PlanTimeline />
      <Divider />
      {/* Chat stream */}
      <div className="flex-1 overflow-y-auto">
        <ChatHistory />
      </div>
      <Divider />
      {/* Input */}
      <div className="p-2">
        <ChatInputArea />
      </div>
    </aside>
  );
};

export default ChatSidebar;
