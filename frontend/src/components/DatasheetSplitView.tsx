import React, { useState, useEffect, Fragment } from 'react';
import { createPortal } from 'react-dom';
import { useDebounce } from 'use-debounce';
import ChatPanel from './ChatPanel';

interface Props {
  assetId: string;
  pdfUrl: string;
  initialParsedData: any;
  onClose: () => void;
  onSave: (id: string, payload: any) => void;
}

export const DatasheetSplitView: React.FC<Props> = ({ assetId, pdfUrl, initialParsedData, onClose, onSave }) => {
  const [data, setData] = useState<any>(initialParsedData);
  const [debounced] = useDebounce(data, 1000);

  useEffect(() => {
    if (JSON.stringify(debounced) !== JSON.stringify(initialParsedData)) {
      onSave(assetId, debounced);
    }
  }, [debounced, assetId, onSave, initialParsedData]);

  const content = (
    <div className="fixed z-50 bg-white shadow-lg left-[240px] top-[108px] right-0 bottom-[40px] grid grid-cols-1 md:grid-cols-2 lg:grid-cols-[1fr_1fr_320px]">
      <div className="h-full border-r border-gray-200">
        <iframe src={pdfUrl} className="w-full h-full" title="PDF Preview" />
      </div>

      <div className="h-full flex flex-col">
        <div className="flex justify-between items-center border-b border-gray-200 bg-gray-50 px-4 py-2">
          <h3 className="text-md font-semibold text-gray-800">Review & Confirm</h3>
          <div className="flex items-center gap-2">
            <button onClick={() => onSave(assetId, data)} className="px-2 py-1 text-sm border rounded">Save</button>
            <button onClick={onClose} className="px-2 py-1 text-sm bg-blue-600 text-white rounded">Confirm &amp; Close</button>
          </div>
        </div>

        <div className="flex-grow overflow-y-auto">
          <ParsedDataForm data={data} onDataChange={setData} />
        </div>

        <div className="border-t border-gray-200 bg-gray-50 h-60">
          <ChatPanel />
        </div>
      </div>
    </div>
  );

  return createPortal(content, document.getElementById('datasheet-overlay-root')!);
};

const FormInput: React.FC<{ label: string; value: string; onChange: (v: string) => void }> = ({ label, value, onChange }) => (
  <div className="mb-4">
    <label className="block text-sm font-medium text-gray-700 capitalize">{label.replace(/_/g, ' ')}</label>
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
    />
  </div>
);

const ParsedDataForm: React.FC<{ data: any; onDataChange: (d: any) => void }> = ({ data = {}, onDataChange }) => {
  const handleFieldChange = (field: string, value: any) => {
    onDataChange({ ...data, [field]: value });
  };

  const handleNestedChange = (group: string, key: string, value: any) => {
    onDataChange({
      ...data,
      [group]: {
        ...(data[group] || {}),
        [key]: value,
      },
    });
  };

  const renderObjectFields = (obj: any, groupName: string) => {
    if (!obj || typeof obj !== 'object') return null;
    return Object.entries(obj).map(([key, value]) => (
      <FormInput
        key={`${groupName}-${key}`}
        label={key}
        value={String(value)}
        onChange={(v) => handleNestedChange(groupName, key, v)}
      />
    ));
  };

  return (
    <div className="p-6">
      {Object.entries(data).map(([key, value]) => {
        if (typeof value === 'object' && value !== null) {
          return (
            <Fragment key={key}>
              <h3 className="text-lg font-semibold text-gray-900 capitalize mt-6 mb-4 border-b pb-2">{key.replace(/_/g, ' ')}</h3>
              {renderObjectFields(value, key)}
            </Fragment>
          );
        }
        return (
          <FormInput
            key={key}
            label={key}
            value={String(value)}
            onChange={(v) => handleFieldChange(key, v)}
          />
        );
      })}
    </div>
  );
};
