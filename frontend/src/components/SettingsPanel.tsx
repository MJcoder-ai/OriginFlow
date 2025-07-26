import React from 'react';
import { useAppStore } from '../appStore';

/**
 * A panel that exposes parsing configuration options to the user.
 * Toggling these checkboxes updates the Zustand store flags which
 * correspond to backend settings.
 */
const SettingsPanel: React.FC = () => {
  const useRuleBased = useAppStore((s) => s.useRuleBased);
  const useTableExtraction = useAppStore((s) => s.useTableExtraction);
  const useAiExtraction = useAppStore((s) => s.useAiExtraction);
  const useOcrFallback = useAppStore((s) => s.useOcrFallback);
  const setExtractionSetting = useAppStore((s) => s.setExtractionSetting);

  const renderSetting = (
    key: 'useRuleBased' | 'useTableExtraction' | 'useAiExtraction' | 'useOcrFallback',
    label: string,
    value: boolean,
  ) => (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm font-medium text-gray-700">{label}</span>
      <label className="inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          className="form-checkbox h-4 w-4 text-blue-600"
          checked={value}
          onChange={(e) => setExtractionSetting(key, e.target.checked)}
        />
      </label>
    </div>
  );

  return (
    <div className="flex flex-col h-full p-4 overflow-auto bg-gray-50 text-black">
      <h2 className="text-lg font-semibold mb-4">Settings</h2>
      <p className="text-sm text-gray-600 mb-6">
        Configure how datasheets are parsed. These options control the backend
        extraction pipeline. You can enable or disable rule-based parsing,
        table extraction, AI extraction and OCR fallback. Changes take effect
        immediately for future parses.
      </p>
      {renderSetting('useRuleBased', 'Use rule-based parsing', useRuleBased)}
      {renderSetting('useTableExtraction', 'Use table extraction', useTableExtraction)}
      {renderSetting('useAiExtraction', 'Use AI extraction', useAiExtraction)}
      {renderSetting('useOcrFallback', 'Use OCR fallback', useOcrFallback)}
    </div>
  );
};

export default SettingsPanel;
