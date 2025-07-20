import React, { useState, useEffect, Fragment } from 'react';
import { useDebounce } from 'use-debounce';

interface Props {
  assetId: string;
  pdfUrl: string;
  initialParsedData: any;
  onClose: () => void;
  onSave: (id: string, payload: any) => void;
}

const DatasheetSplitView: React.FC<Props> = ({ assetId, pdfUrl, initialParsedData, onClose, onSave }) => {
  const [data, setData] = useState<any>(initialParsedData);
  const [debounced] = useDebounce(data, 1000);

  useEffect(() => {
    if (JSON.stringify(debounced) !== JSON.stringify(initialParsedData)) {
      onSave(assetId, debounced);
    }
  }, [debounced, assetId, onSave, initialParsedData]);

  return (
    <div className="flex flex-1 w-full h-full">
      <div className="w-1/2 h-full border-r border-gray-200">
        <iframe src={pdfUrl} className="w-full h-full" title="PDF Preview" />
      </div>
      <div className="w-1/2 h-full flex flex-col overflow-y-auto">
        <div className="flex justify-between items-center px-4 py-2 bg-gray-50 border-b">
          <h2 className="text-md font-bold text-gray-800">Review & Confirm</h2>
          <div className="space-x-2">
            <button onClick={() => onSave(assetId, data)} className="px-3 py-1 border text-sm rounded hover:bg-gray-100">Save</button>
            <button onClick={onClose} className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">Confirm & Close</button>
          </div>
        </div>
        <div className="p-4 space-y-4">
          {Object.entries(data).map(([key, value]) => (
            <div key={key} className="flex flex-col">
              <label className="text-sm font-medium text-gray-700">{key}</label>
              <input type="text" value={value as any} onChange={(e) => setData({ ...data, [key]: e.target.value })} className="border px-2 py-1 text-sm rounded" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const FormInput: React.FC<{ label: string; value: string; onChange: (v: string) => void }> = ({ label, value, onChange }) => (
  <div className="grid grid-cols-3 gap-4 items-center">
    <label className="text-sm font-medium text-gray-600 capitalize text-right">{label.replace(/_/g, ' ')}</label>
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="col-span-2 mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
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
    <div className="p-6 space-y-4">
      {Object.entries(data).map(([key, value]) => {
        if (typeof value === 'object' && value !== null) {
          return (
            <Fragment key={key}>
              <h3 className="text-lg font-semibold text-gray-900 capitalize mt-6 mb-4 border-b pb-2">{key.replace(/_/g, ' ')}</h3>
              <div className="space-y-4">{renderObjectFields(value, key)}</div>
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

export default DatasheetSplitView;
