import React, { useEffect, useState, useCallback } from 'react';
import { useAppStore } from '../appStore';

interface ODLCodeViewProps {
  sessionId: string;
}

interface ODLTextData {
  text: string;
  version: number;
  node_count: number;
  edge_count: number;
  last_updated?: string;
}

export const ODLCodeView: React.FC<ODLCodeViewProps> = ({ sessionId }) => {
  const [odlData, setOdlData] = useState<ODLTextData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const { addStatusMessage } = useAppStore();

  const fetchODLText = useCallback(async () => {
    if (!sessionId || loading) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await fetch(`/api/v1/odl/sessions/${sessionId}/text`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`Failed to fetch ODL text: ${response.statusText}`);
          }
          return response.json();
        });
      setOdlData(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      setOdlData({
        text: `# Error loading ODL text\n# ${errorMessage}\n\n# Please check your session ID and try again`,
        version: 0,
        node_count: 0,
        edge_count: 0
      });
      addStatusMessage('Failed to load ODL text', 'error');
    } finally {
      setLoading(false);
    }
  }, [sessionId, loading, addStatusMessage]);

  useEffect(() => {
    fetchODLText();
  }, [fetchODLText]);

  // Auto-refresh every 5 seconds when enabled
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(fetchODLText, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchODLText]);

  const handleRefresh = () => {
    fetchODLText();
  };

  const copyToClipboard = async () => {
    if (!odlData?.text) return;
    
    try {
      await navigator.clipboard.writeText(odlData.text);
      addStatusMessage('ODL code copied to clipboard', 'success');
    } catch (err) {
      addStatusMessage('Failed to copy to clipboard', 'error');
    }
  };

  const downloadAsFile = () => {
    if (!odlData?.text) return;
    
    const blob = new Blob([odlData.text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `odl-design-v${odlData.version}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    addStatusMessage('ODL code downloaded', 'success');
  };

  if (!sessionId) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-gray-500 mb-2">No active session</div>
          <div className="text-sm text-gray-400">
            Start designing to see ODL code
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">ODL Code View</h3>
            <p className="text-sm text-gray-600">
              Live representation of your design in ODL format
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1 rounded text-sm ${
                autoRefresh 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'bg-gray-100 text-gray-700'
              }`}
              title={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh'}
            >
              {autoRefresh ? '🔄 Auto' : '⏸️ Manual'}
            </button>
            
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200 disabled:opacity-50"
              title="Refresh now"
            >
              🔄 Refresh
            </button>
            
            <button
              onClick={copyToClipboard}
              disabled={!odlData?.text}
              className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200 disabled:opacity-50"
              title="Copy to clipboard"
            >
              📋 Copy
            </button>
            
            <button
              onClick={downloadAsFile}
              disabled={!odlData?.text}
              className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200 disabled:opacity-50"
              title="Download as file"
            >
              💾 Download
            </button>
          </div>
        </div>
        
        {/* Stats bar */}
        {odlData && (
          <div className="mt-3 flex items-center space-x-4 text-xs text-gray-500">
            <span>Version: {odlData.version}</span>
            <span>Nodes: {odlData.node_count}</span>
            <span>Edges: {odlData.edge_count}</span>
            <span>Lines: {odlData.text.split('\n').length}</span>
            {odlData.last_updated && (
              <span>Updated: {new Date(odlData.last_updated).toLocaleTimeString()}</span>
            )}
            {loading && <span className="text-blue-500">Refreshing...</span>}
          </div>
        )}
        
        {error && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            Error: {error}
          </div>
        )}
      </div>
      
      {/* Code content */}
      <div className="flex-1 overflow-auto">
        <pre className="p-4 text-sm font-mono bg-gray-50 h-full overflow-auto leading-relaxed">
          <code className="odl-syntax">
            {odlData?.text || '# No design data\n# Start by creating a design to see ODL code here'}
          </code>
        </pre>
      </div>
      
      {/* Footer */}
      <div className="flex-shrink-0 p-2 border-t border-gray-200 bg-white">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-4">
            <span>Session: {sessionId.slice(0, 8)}...</span>
            {odlData && (
              <span className="text-green-600">
                ✓ {odlData.text.split('\n').filter(line => line.trim() && !line.startsWith('#')).length} active lines
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <span>ODL Format</span>
            {autoRefresh && <span className="text-blue-500">Auto-updating</span>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ODLCodeView;
