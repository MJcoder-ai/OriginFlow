import React, { useState, useEffect, Fragment } from 'react';
import { useDebounce } from 'use-debounce';

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
    if (debounced !== initialParsedData) {
      onSave(assetId, debounced);
    }
  }, [debounced, assetId, onSave, initialParsedData]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center border-b bg-gray-50 px-3 py-2">
        <h3 className="m-0 text-sm font-medium">Datasheet Viewer</h3>
        <button onClick={onClose} className="text-lg leading-none">&times;</button>
      </div>
      <div className="flex-grow grid grid-cols-2">
        <div className="h-full">
          <iframe src={pdfUrl} className="w-full h-full border-r" title="PDF Preview" />
        </div>
        <div className="h-full overflow-y-auto">
          <ParsedDataForm data={data} onDataChange={setData} />
        </div>
      </div>
    </div>
  );
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
