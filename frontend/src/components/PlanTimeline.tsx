/**
 * File: frontend/src/components/PlanTimeline.tsx
 * Visualisation of high‑level AI tasks in a sequential timeline.
 * Each task includes a status icon and optional description.  When
 * present, the plan timeline appears at the top of the chat history
 * and provides users with an at‑a‑glance overview of the AI’s plan.
 */
import React from 'react';
import { useAppStore, PlanTask } from '../appStore';
import RequirementsForm from './RequirementsForm';
import { CheckCircle, Circle, Loader2, AlertTriangle } from 'lucide-react';

/** Mapping of task status to icon component. */
const statusIcon: Record<PlanTask['status'], React.ElementType> = {
  pending: Circle,
  in_progress: Loader2,
  complete: CheckCircle,
  blocked: AlertTriangle,
};

/** Mapping of task status to Tailwind CSS colour classes. */
const statusColors: Record<PlanTask['status'], string> = {
  pending: 'text-gray-400',
  in_progress: 'text-blue-500',
  complete: 'text-green-600',
  blocked: 'text-yellow-500',
};

const PlanTimeline: React.FC = () => {
  const tasks = useAppStore((s) => s.planTasks);
  const performPlanTask = useAppStore((s) => s.performPlanTask);
  const updatePlanTaskStatus = useAppStore((s) => s.updatePlanTaskStatus);
  if (!tasks || tasks.length === 0) return null;
  const nextStatusFn = (status: PlanTask['status']) => {
    if (status === 'pending') return 'in_progress';
    if (status === 'in_progress') return 'complete';
    return 'pending';
  };
  return (
    <div className="p-4 border-b border-gray-200 bg-gray-50">
      <div className="mb-2 text-xs font-semibold uppercase text-gray-600">Plan</div>
      <ol className="space-y-2">
        {tasks.map((task) => {
          const Icon = statusIcon[task.status];
          const color = statusColors[task.status];
          const isSpinning = task.status === 'in_progress';
          return (
            <li key={task.id} className="flex items-start space-x-2">
              <button
                type="button"
                onClick={() => {
                  const nextStatus = nextStatusFn(task.status);
                  if (nextStatus === 'in_progress') {
                    performPlanTask(task);
                  } else {
                    updatePlanTaskStatus(task.id, nextStatus);
                  }
                }}
                className="flex items-start space-x-2 text-left group focus:outline-none"
                aria-label={`Toggle status for ${task.title}`}
              >
                <Icon
                  className={`h-4 w-4 mt-0.5 ${color} ${isSpinning ? 'animate-spin' : ''}`}
                  aria-hidden="true"
                />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900 group-hover:underline">
                    {task.title}
                  </div>
                  {task.description && (
                    <div className="text-xs text-gray-500 leading-snug">
                      {task.description}
                    </div>
                  )}
                </div>
              </button>
            </li>
          );
        })}
      </ol>
      {/* Show requirements form when gather_requirements is present and pending/blocked */}
      {tasks.some((t) => t.id === 'gather_requirements' && (t.status === 'pending' || t.status === 'blocked')) && (
        <RequirementsForm />
      )}
    </div>
  );
};

export default PlanTimeline;

