/**
 * Undo/Redo Controls Component
 * Provides undo and redo functionality using the versioning API
 */
import React, { useState, useEffect } from 'react';
import { useAppStore } from '../appStore';
import { API_BASE_URL } from '../config';
import { 
  Undo, 
  Redo, 
  History, 
  ChevronDown, 
  ChevronUp,
  Clock,
  GitBranch,
  AlertCircle
} from 'lucide-react';

interface VersionInfo {
  version: number;
  timestamp: string;
  changes: string[];
  canRevert: boolean;
}

interface UndoRedoControlsProps {
  sessionId: string;
  className?: string;
  variant?: 'compact' | 'full';
}

export const UndoRedoControls: React.FC<UndoRedoControlsProps> = ({
  sessionId,
  className = '',
  variant = 'compact'
}) => {
  const { addStatusMessage, canvasComponents, links } = useAppStore();
  const [currentVersion, setCurrentVersion] = useState(0);
  const [versions, setVersions] = useState<VersionInfo[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [isReverting, setIsReverting] = useState(false);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);

  // Track version changes based on canvas state
  useEffect(() => {
    // This is a simplified version tracking - in a real implementation,
    // you'd want to hook into the actual ODL graph changes
    const trackVersion = async () => {
      try {
        // Get current session version (this would come from your ODL session)
        // For now, we'll simulate it based on component/link changes
        const componentCount = canvasComponents.length;
        const linkCount = links.length;
        const newVersion = componentCount + linkCount;
        
        if (newVersion !== currentVersion) {
          setCurrentVersion(newVersion);
          setCanUndo(newVersion > 0);
          setCanRedo(false); // Reset redo when new changes are made
        }
      } catch (error) {
        console.error('Error tracking version:', error);
      }
    };

    trackVersion();
  }, [canvasComponents, links, currentVersion]);

  // Fetch version history
  const fetchVersionHistory = async () => {
    try {
      // This would call your versioning API to get patch history
      // For now, we'll simulate some version data
      const mockVersions: VersionInfo[] = [
        {
          version: 0,
          timestamp: new Date(Date.now() - 60000).toISOString(),
          changes: ['Initial design'],
          canRevert: false
        },
        {
          version: 1,
          timestamp: new Date(Date.now() - 30000).toISOString(),
          changes: ['Added solar panel', 'Added inverter'],
          canRevert: true
        },
        {
          version: 2,
          timestamp: new Date().toISOString(),
          changes: ['Connected components', 'Added wiring'],
          canRevert: true
        }
      ];
      
      setVersions(mockVersions);
    } catch (error) {
      console.error('Error fetching version history:', error);
      addStatusMessage('Failed to fetch version history', 'error');
    }
  };

  // Handle undo operation
  const handleUndo = async () => {
    if (!canUndo || isReverting) return;

    setIsReverting(true);
    try {
      const targetVersion = Math.max(0, currentVersion - 1);
      
      const response = await fetch(`${API_BASE_URL}/versions/${sessionId}/revert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target_version: targetVersion
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to revert: ${response.statusText}`);
      }

      const result = await response.json();
      setCurrentVersion(result.version);
      setCanUndo(result.version > 0);
      setCanRedo(true);
      
      addStatusMessage(`Reverted to version ${result.version}`, 'success');
      
      // Refresh the canvas state (this would trigger a reload of the ODL graph)
      // In a real implementation, you'd call a function to reload the canvas
      
    } catch (error) {
      console.error('Undo failed:', error);
      addStatusMessage('Undo operation failed', 'error');
    } finally {
      setIsReverting(false);
    }
  };

  // Handle redo operation
  const handleRedo = async () => {
    if (!canRedo || isReverting) return;

    setIsReverting(true);
    try {
      const targetVersion = currentVersion + 1;
      
      const response = await fetch(`${API_BASE_URL}/versions/${sessionId}/revert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target_version: targetVersion
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to redo: ${response.statusText}`);
      }

      const result = await response.json();
      setCurrentVersion(result.version);
      setCanRedo(false); // Usually can't redo after a redo unless there are more versions
      
      addStatusMessage(`Advanced to version ${result.version}`, 'success');
      
    } catch (error) {
      console.error('Redo failed:', error);
      addStatusMessage('Redo operation failed', 'error');
    } finally {
      setIsReverting(false);
    }
  };

  // Handle revert to specific version
  const handleRevertToVersion = async (targetVersion: number) => {
    if (isReverting || targetVersion === currentVersion) return;

    setIsReverting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/versions/${sessionId}/revert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target_version: targetVersion
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to revert: ${response.statusText}`);
      }

      const result = await response.json();
      setCurrentVersion(result.version);
      setCanUndo(result.version > 0);
      setCanRedo(result.version < versions.length - 1);
      setShowHistory(false);
      
      addStatusMessage(`Reverted to version ${result.version}`, 'success');
      
    } catch (error) {
      console.error('Revert failed:', error);
      addStatusMessage('Revert operation failed', 'error');
    } finally {
      setIsReverting(false);
    }
  };

  // Get version diff
  const getVersionDiff = async (fromVersion: number, toVersion: number) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/versions/${sessionId}/diff?from_version=${fromVersion}&to_version=${toVersion}`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to get diff: ${response.statusText}`);
      }
      
      const result = await response.json();
      return result.patches;
    } catch (error) {
      console.error('Error fetching diff:', error);
      return null;
    }
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  // Compact variant for toolbar
  if (variant === 'compact') {
    return (
      <div className={`flex items-center space-x-1 ${className}`}>
        <button
          onClick={handleUndo}
          disabled={!canUndo || isReverting}
          className="p-2 text-gray-500 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Undo"
        >
          <Undo size={18} />
        </button>
        
        <button
          onClick={handleRedo}
          disabled={!canRedo || isReverting}
          className="p-2 text-gray-500 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Redo"
        >
          <Redo size={18} />
        </button>
        
        <button
          onClick={() => {
            setShowHistory(!showHistory);
            if (!showHistory) fetchVersionHistory();
          }}
          className="p-2 text-gray-500 hover:text-blue-600 transition-colors"
          title="Version History"
        >
          <History size={18} />
        </button>

        {/* History dropdown */}
        {showHistory && (
          <div className="absolute top-full left-0 mt-1 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
            <div className="p-3 border-b border-gray-100">
              <h3 className="text-sm font-semibold text-gray-900 flex items-center">
                <GitBranch className="w-4 h-4 mr-2" />
                Version History
              </h3>
            </div>
            
            <div className="max-h-64 overflow-y-auto">
              {versions.map((version) => (
                <div
                  key={version.version}
                  className={`p-3 border-b border-gray-50 hover:bg-gray-50 cursor-pointer ${
                    version.version === currentVersion ? 'bg-blue-50 border-blue-200' : ''
                  }`}
                  onClick={() => handleRevertToVersion(version.version)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className={`text-sm font-medium ${
                        version.version === currentVersion ? 'text-blue-700' : 'text-gray-900'
                      }`}>
                        Version {version.version}
                      </span>
                      {version.version === currentVersion && (
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                          Current
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-500">
                      {formatTimestamp(version.timestamp)}
                    </span>
                  </div>
                  
                  <div className="mt-1">
                    {version.changes.map((change, index) => (
                      <div key={index} className="text-xs text-gray-600">
                        • {change}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Full variant for sidebar or panel
  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      <div className="p-4 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-900 flex items-center">
          <GitBranch className="w-4 h-4 mr-2" />
          Version Control
        </h3>
        <p className="text-xs text-gray-500 mt-1">
          Current: Version {currentVersion}
        </p>
      </div>

      {/* Action buttons */}
      <div className="p-4 space-y-3">
        <div className="flex space-x-2">
          <button
            onClick={handleUndo}
            disabled={!canUndo || isReverting}
            className="flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed rounded-md transition-colors"
          >
            <Undo className="w-4 h-4 mr-2" />
            Undo
          </button>
          
          <button
            onClick={handleRedo}
            disabled={!canRedo || isReverting}
            className="flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed rounded-md transition-colors"
          >
            <Redo className="w-4 h-4 mr-2" />
            Redo
          </button>
        </div>

        {isReverting && (
          <div className="flex items-center space-x-2 text-sm text-blue-600">
            <Clock className="w-4 h-4 animate-pulse" />
            <span>Reverting...</span>
          </div>
        )}
      </div>

      {/* Version history */}
      <div className="border-t border-gray-100">
        <button
          onClick={() => {
            setShowHistory(!showHistory);
            if (!showHistory) fetchVersionHistory();
          }}
          className="w-full flex items-center justify-between p-4 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        >
          <span className="flex items-center">
            <History className="w-4 h-4 mr-2" />
            Version History
          </span>
          {showHistory ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {showHistory && (
          <div className="border-t border-gray-100 max-h-64 overflow-y-auto">
            {versions.map((version) => (
              <div
                key={version.version}
                className={`p-4 border-b border-gray-50 cursor-pointer hover:bg-gray-50 ${
                  version.version === currentVersion ? 'bg-blue-50' : ''
                }`}
                onClick={() => handleRevertToVersion(version.version)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className={`text-sm font-medium ${
                      version.version === currentVersion ? 'text-blue-700' : 'text-gray-900'
                    }`}>
                      Version {version.version}
                    </span>
                    {version.version === currentVersion && (
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                        Current
                      </span>
                    )}
                  </div>
                  {!version.canRevert && (
                    <AlertCircle className="w-4 h-4 text-gray-400" title="Cannot revert to this version" />
                  )}
                </div>
                
                <div className="text-xs text-gray-500 mb-2">
                  {formatTimestamp(version.timestamp)}
                </div>
                
                <div className="space-y-1">
                  {version.changes.map((change, index) => (
                    <div key={index} className="text-xs text-gray-600 flex items-center">
                      <span className="w-1 h-1 bg-gray-400 rounded-full mr-2"></span>
                      {change}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default UndoRedoControls;
