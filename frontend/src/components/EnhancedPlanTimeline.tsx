import React, { useState, useEffect } from 'react';
import { useAppStore } from '../appStore';
import { API_BASE_URL } from '../config'; // Import base URL for API calls

interface PlanTask {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'complete' | 'blocked';
  reason?: string;
  estimated_panels?: number;
  estimated_inverters?: number;
  placeholder_summary?: string;
  estimated_selections?: number;
  design_completeness?: number;
  missing_requirements?: string[];
  missing_components?: string[];
  can_use_placeholders?: boolean;
}

interface EnhancedPlanTimelineProps {
  sessionId: string;
  tasks: PlanTask[];
  onRunTask: (taskId: string) => void;
  onShowRequirements: () => void;
  onUploadComponents: () => void;
  onShowComponentSelection: (taskId: string) => void;
}

export const EnhancedPlanTimeline: React.FC<EnhancedPlanTimelineProps> = ({
  sessionId,
  tasks,
  onRunTask,
  onShowRequirements,
  onUploadComponents,
  onShowComponentSelection
}) => {
  const [refreshing, setRefreshing] = useState(false);
  const [taskProgress, setTaskProgress] = useState<Record<string, number>>({});
  const { addStatusMessage } = useAppStore();

  // Auto-refresh task list periodically
  useEffect(() => {
    const interval = setInterval(async () => {
      if (sessionId && !refreshing) {
        await refreshTaskList();
      }
    }, 10000); // Refresh every 10 seconds

    return () => clearInterval(interval);
  }, [sessionId, refreshing]);

  const refreshTaskList = async () => {
    if (!sessionId) return;
    
    setRefreshing(true);
    try {
      // Use API_BASE_URL to target the backend; relative URLs would hit the frontend dev server instead.
      const response = await fetch(`${API_BASE_URL}/odl/sessions/${sessionId}/plan?command=design system`);
      if (response.ok) {
        const data = await response.json();
        // This would update the task list, but since it's passed as props,
        // we'll just indicate success
      }
    } catch (error) {
      console.warn('Failed to refresh task list:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const getTaskIcon = (taskId: string, status: string) => {
    const icons = {
      gather_requirements: '📋',
      generate_design: '🎨', 
      generate_structural: '🏗️',
      generate_wiring: '⚡',
      populate_real_components: '🔧',
      generate_battery: '🔋',
      generate_monitoring: '📊',
      refine_validate: '✅'
    };
    
    if (status === 'complete') return '✅';
    if (status === 'in_progress') return '⏳';
    if (status === 'blocked') return '🚫';
    
    return icons[taskId as keyof typeof icons] || '📝';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete': return 'text-green-600 bg-green-100 border-green-200';
      case 'in_progress': return 'text-blue-600 bg-blue-100 border-blue-200'; 
      case 'blocked': return 'text-red-600 bg-red-100 border-red-200';
      default: return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const getTaskBorderColor = (status: string) => {
    switch (status) {
      case 'complete': return 'border-green-200 bg-green-50';
      case 'in_progress': return 'border-blue-200 bg-blue-50';
      case 'blocked': return 'border-red-200 bg-red-50';
      case 'pending': return 'border-blue-200 bg-blue-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const handleTaskAction = async (task: PlanTask) => {
    if (task.status === 'blocked') {
      // Handle blocked tasks with specific actions
      if (task.id === 'gather_requirements') {
        if (task.missing_requirements?.length) {
          onShowRequirements();
        } else if (task.missing_components?.length) {
          onUploadComponents();
        }
      } else if (task.missing_components?.length) {
        onUploadComponents();
      } else {
        addStatusMessage(`Task ${task.title} is blocked: ${task.reason}`, 'warning');
      }
    } else if (task.status === 'pending') {
      if (task.id === 'populate_real_components') {
        onShowComponentSelection(task.id);
      } else {
        setTaskProgress({ ...taskProgress, [task.id]: 0 });
        try {
          await onRunTask(task.id);
          setTaskProgress({ ...taskProgress, [task.id]: 100 });
        } catch (error) {
          setTaskProgress({ ...taskProgress, [task.id]: 0 });
        }
      }
    }
  };

  const getCompletionPercentage = () => {
    if (tasks.length === 0) return 0;
    const completedTasks = tasks.filter(t => t.status === 'complete').length;
    return (completedTasks / tasks.length) * 100;
  };

  const getTaskDescription = (task: PlanTask) => {
    let description = task.description || task.reason || '';
    
    // Add helpful context based on task type
    if (task.id === 'gather_requirements' && task.missing_requirements?.length) {
      description += ` Missing: ${task.missing_requirements.join(', ')}`;
    }
    
    if (task.id === 'generate_design' && task.estimated_panels) {
      description += ` (Est. ${task.estimated_panels} panels, ${task.estimated_inverters} inverters)`;
    }
    
    if (task.id === 'populate_real_components' && task.placeholder_summary) {
      description += ` Replace: ${task.placeholder_summary}`;
    }
    
    return description;
  };

  const getActionButtonText = (task: PlanTask) => {
    if (task.status === 'blocked') {
      if (task.missing_requirements?.length) return 'Enter Requirements';
      if (task.missing_components?.length) return 'Upload Components';
      return 'Fix Issues';
    }
    
    if (task.status === 'pending') {
      if (task.id === 'populate_real_components') return 'Select Components';
      return 'Run Task';
    }
    
    return 'View';
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Design Plan</h3>
          <p className="text-sm text-gray-600">
            {tasks.length} tasks • {getCompletionPercentage().toFixed(0)}% complete
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={refreshTaskList}
            disabled={refreshing}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
            title="Refresh task list"
          >
            {refreshing ? '🔄' : '↻'} Refresh
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      {tasks.length > 0 && (
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${getCompletionPercentage()}%` }}
          />
        </div>
      )}
      
      {/* Task List */}
      {tasks.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">🚀</div>
          <p className="text-lg font-medium">No active design plan</p>
          <p className="text-sm">Start by asking the AI to design a system</p>
        </div>
      ) : (
        <div className="space-y-3">
          {tasks.map((task, index) => (
            <div
              key={task.id}
              className={`p-4 rounded-lg border-2 transition-all ${getTaskBorderColor(task.status)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <div className="flex-shrink-0">
                    <span className="text-2xl">
                      {getTaskIcon(task.id, task.status)}
                    </span>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900">{task.title}</h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                        {task.status}
                      </span>
                    </div>
                    
                    {getTaskDescription(task) && (
                      <p className="text-sm text-gray-600 mt-1">
                        {getTaskDescription(task)}
                      </p>
                    )}
                    
                    {/* Task-specific details */}
                    {task.id === 'populate_real_components' && task.estimated_selections && (
                      <div className="mt-2 p-2 bg-yellow-50 rounded text-sm">
                        <p className="text-yellow-800">
                          <strong>Components to select:</strong> {task.estimated_selections}
                        </p>
                      </div>
                    )}
                    
                    {task.design_completeness !== undefined && (
                      <div className="mt-2">
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <span>Design Completeness:</span>
                          <div className="w-20 bg-gray-200 rounded-full h-1">
                            <div 
                              className="bg-blue-600 h-1 rounded-full"
                              style={{ width: `${task.design_completeness * 100}%` }}
                            />
                          </div>
                          <span>{(task.design_completeness * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    )}

                    {/* Missing requirements/components indicators */}
                    {task.missing_requirements && task.missing_requirements.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {task.missing_requirements.map(req => (
                          <span key={req} className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">
                            Missing: {req.replace('_', ' ')}
                          </span>
                        ))}
                      </div>
                    )}

                    {task.missing_components && task.missing_components.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {task.missing_components.map(comp => (
                          <span key={comp} className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded">
                            Need: {comp} datasheet
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Action Button */}
                <div className="flex-shrink-0 ml-4">
                  {(task.status === 'pending' || task.status === 'blocked') && (
                    <button
                      onClick={() => handleTaskAction(task)}
                      className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                        task.status === 'pending' 
                          ? 'bg-blue-600 text-white hover:bg-blue-700' 
                          : 'bg-orange-600 text-white hover:bg-orange-700'
                      }`}
                      disabled={taskProgress[task.id] > 0 && taskProgress[task.id] < 100}
                    >
                      {taskProgress[task.id] > 0 && taskProgress[task.id] < 100 ? (
                        <span className="flex items-center space-x-2">
                          <span>⏳</span>
                          <span>{taskProgress[task.id]}%</span>
                        </span>
                      ) : (
                        getActionButtonText(task)
                      )}
                    </button>
                  )}
                  
                  {task.status === 'complete' && (
                    <div className="flex items-center text-green-600 text-sm">
                      <span className="mr-1">✓</span>
                      Complete
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Quick Actions */}
      {tasks.length > 0 && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Quick Actions</h4>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={onShowRequirements}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
            >
              📋 Edit Requirements
            </button>
            <button
              onClick={onUploadComponents}
              className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
            >
              📁 Upload Components
            </button>
            <button
              onClick={refreshTaskList}
              className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700"
            >
              🔄 Refresh Plan
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedPlanTimeline;
