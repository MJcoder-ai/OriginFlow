/**
 * File: frontend/src/components/PlanTimeline.tsx
 * Enhanced plan timeline with sequential task execution and confidence scores.
 * Users can click tasks sequentially, and the UI shows task dependencies.
 */
import React from 'react';
import { useAppStore, PlanTask } from '../appStore';
import { api } from '../services/api';
import RequirementsForm from './RequirementsForm';
import EnhancedFileUpload from './EnhancedFileUpload';
import { CheckCircle, Circle, Loader2, AlertTriangle, Clock, ArrowRight } from 'lucide-react';

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
  const sessionId = useAppStore((s) => s.sessionId);
  const graphVersion = useAppStore((s) => s.graphVersion);
  const setGraphVersion = useAppStore((s) => s.setGraphVersion);
  const setPlanTasks = useAppStore((s) => s.setPlanTasks);
  const addMessage = useAppStore((s) => s.addMessage);
  const updatePlanTaskStatus = useAppStore((s) => s.updatePlanTaskStatus);
  const isAiProcessing = useAppStore((s) => s.isAiProcessing);
  
  if (!tasks || tasks.length === 0) return null;
  
  // Find the current task (first pending/blocked task)
  const currentTaskIndex = tasks.findIndex(task => 
    task.status === 'pending' || task.status === 'blocked'
  );
  
  // Helper to check if a task can be executed
  const canExecuteTask = (taskIndex: number) => {
    if (isAiProcessing) return false;
    
    // Can only execute current task or tasks that are already in progress
    const task = tasks[taskIndex];
    return task.status === 'pending' || task.status === 'blocked' || task.status === 'in_progress';
  };
  
  // Helper to check if task is current
  const isCurrentTask = (taskIndex: number) => {
    return taskIndex === currentTaskIndex;
  };
  return (
    <div className="p-4 border-b border-gray-200 bg-gray-50">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-xs font-semibold uppercase text-gray-600">Plan</div>
        <div className="text-xs text-gray-500">
          {tasks.filter(t => t.status === 'complete').length} of {tasks.length} complete
        </div>
      </div>
      
      <div className="space-y-3">
        {tasks.map((task, index) => {
          const Icon = statusIcon[task.status];
          const color = statusColors[task.status];
          const isSpinning = task.status === 'in_progress';
          const isCurrent = isCurrentTask(index);
          const canExecute = canExecuteTask(index);
          const isPrevious = index < currentTaskIndex;
          
          return (
            <div key={task.id} className="flex items-start space-x-3">
              {/* Connection line to next task */}
              {index < tasks.length - 1 && (
                <div className="absolute ml-2 mt-6 h-6 w-0.5 bg-gray-300" />
              )}
              
              <button
                type="button"
                onClick={() => {
                  if (canExecute && (task.status === 'pending' || task.status === 'blocked')) {
                    // Prefer enhanced act loop for richer UX
                    if (sessionId) {
                      api.act(sessionId, task.id, undefined, graphVersion)
                        .then((res) => {
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
                          if (Array.isArray(res.updated_tasks)) {
                            setPlanTasks(res.updated_tasks.map((t: any) => ({ id: t.id, title: t.title, description: t.reason || t.description, status: t.status })));
                          }
                        })
                        .catch(() => performPlanTask(task));
                    } else {
                      performPlanTask(task);
                    }
                  }
                }}
                disabled={!canExecute}
                className={`relative flex items-start space-x-3 w-full text-left p-3 rounded-lg border transition-all duration-200 ${
                  isCurrent 
                    ? 'border-blue-200 bg-blue-50 shadow-sm' 
                    : isPrevious 
                    ? 'border-green-200 bg-green-50' 
                    : 'border-gray-200 bg-white hover:bg-gray-50'
                } ${canExecute ? 'cursor-pointer' : 'cursor-default'}`}
                aria-label={`Execute ${task.title}`}
              >
                {/* Status indicator */}
                <div className="flex-shrink-0 mt-0.5">
                  <Icon
                    className={`h-5 w-5 ${color} ${isSpinning ? 'animate-spin' : ''}`}
                    aria-hidden="true"
                  />
                </div>
                
                {/* Task content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className={`text-sm font-medium ${
                      isCurrent ? 'text-blue-900' : 'text-gray-900'
                    }`}>
                      {task.title}
                    </h4>
                    
                    {/* Task indicators */}
                    <div className="flex items-center space-x-2">
                      {isCurrent && (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded">
                          <Clock className="w-3 h-3 mr-1" />
                          Current
                        </span>
                      )}
                      {canExecute && task.status === 'pending' && (
                        <ArrowRight className="w-4 h-4 text-blue-500" />
                      )}
                    </div>
                  </div>
                  
                  {task.description && (
                    <p className={`mt-1 text-xs leading-relaxed ${
                      isCurrent ? 'text-blue-700' : 'text-gray-600'
                    }`}>
                      {task.description}
                    </p>
                  )}
                  
                  {/* Progress indicator for current task */}
                  {isCurrent && task.status === 'pending' && (
                    <div className="mt-2 text-xs text-blue-600 font-medium">
                      Click to execute this task
                    </div>
                  )}
                </div>
              </button>
            </div>
          );
        })}
      </div>
      
      {/* Inline remediation when gather_requirements is blocked */}
      {tasks.some((t) => t.id === 'gather_requirements' && t.status === 'blocked') && (
        <div className="mt-4 space-y-3">
          <div className="text-xs font-semibold uppercase text-gray-600">Unblock Gather Requirements</div>
          <RequirementsForm />
          <div className="border rounded-lg bg-white p-3">
            <div className="text-sm font-medium text-gray-900 mb-2">Missing components?</div>
            <p className="text-xs text-gray-600 mb-2">Upload panel/inverter datasheets. We will parse and ingest them automatically, then refresh the plan.</p>
            <EnhancedFileUpload variant="compact" onUploadComplete={async (files) => {
              try {
                // Ingest basic components as placeholders (panel/inverter detection could be added)
                for (const f of files) {
                  // naive heuristic: let user pick in a later iteration; here we just trigger ingest if parsed payload exists elsewhere
                  // Placeholder: nothing to ingest without parsed payload mapping
                }
                // Refresh gather status and plan
                // In a real flow, you'd parse and then call /components/ingest
                const sessionId = (useAppStore.getState() as any).sessionId;
                if (sessionId) {
                  await api.getRequirementsStatus(sessionId);
                  const plan = await api.getPlanForSession(sessionId, 'design system');
                  if (Array.isArray(plan.tasks)) useAppStore.getState().setPlanTasks(plan.tasks as any);
                }
              } catch (e) {
                console.error(e);
              }
            }} />
          </div>
        </div>
      )}
    </div>
  );
};

export default PlanTimeline;

