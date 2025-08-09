/**
 * File: frontend/src/components/ModeSelector.tsx
 * Provides a dropdown for selecting the high‑level chat mode.  Each
 * mode toggles different AI capabilities and influences how prompts
 * are interpreted.  This selector is typically placed near the chat
 * input to allow quick switching between design, analysis, manual and
 * business contexts.
 */
import React from 'react';
import { useAppStore } from '../appStore';

const ModeSelector: React.FC = () => {
  const currentMode = useAppStore((s) => s.currentMode);
  const setCurrentMode = useAppStore((s) => s.setCurrentMode);
  return (
    <div className="flex items-center space-x-2">
      <label htmlFor="mode-select" className="text-sm text-gray-700 font-medium">
        Mode:
      </label>
      <select
        id="mode-select"
        value={currentMode}
        onChange={(e) => setCurrentMode(e.target.value as any)}
        className="border border-gray-300 text-sm rounded-md px-2 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="design">Design</option>
        <option value="analyze">Analyze</option>
        <option value="manual">Manual</option>
        <option value="business">Business</option>
      </select>
    </div>
  );
};

export default ModeSelector;

