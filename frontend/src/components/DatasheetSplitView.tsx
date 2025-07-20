import React, { useState, useEffect } from 'react';
import { useDebounce } from 'use-debounce';

interface Props {
  assetId: string;
  pdfUrl: string;
  initialParsedData: any;
  onClose: () => void;
  onSave: (id: string, payload: any) => void;
}

export const DatasheetSplitView: React.FC<Props> = ({ assetId, pdfUrl, initialParsedData, onClose, onSave }) => {
  const [json, setJson] = useState<any>(initialParsedData);
  const [debounced] = useDebounce(json, 1000);

  useEffect(() => {
    if (debounced !== initialParsedData) {
      onSave(assetId, debounced);
    }
  }, [debounced, assetId, onSave, initialParsedData]);

  return (
    <div style={overlay}>
      <div style={container}>
        <div style={header}>
          <h3 style={{ margin: 0 }}>Datasheet Viewer</h3>
          <button onClick={onClose} style={closeButton}>&times;</button>
        </div>
        <div style={content}>
          <div style={pane}>
            <iframe src={pdfUrl} style={{ width: '100%', height: '100%', border: 'none' }} title="PDF" />
          </div>
          <div style={pane}>
            <ParsedDataForm data={json} onDataChange={setJson} />
          </div>
        </div>
      </div>
    </div>
  );
};

const overlay: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  background: 'rgba(0,0,0,0.5)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
};

const container: React.CSSProperties = {
  width: '80%',
  height: '80%',
  background: 'white',
  display: 'flex',
  flexDirection: 'column',
};

const header: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '0.5rem 1rem',
  borderBottom: '1px solid #ddd',
};

const content: React.CSSProperties = {
  flex: 1,
  display: 'flex',
};

const pane: React.CSSProperties = {
  flex: 1,
  overflow: 'auto',
};

const ParsedDataForm: React.FC<{ data: any; onDataChange: (d: any) => void }> = ({ data, onDataChange }) => {
  const handleChange = (field: string, value: any) => {
    onDataChange({ ...data, [field]: value });
  };

  return (
    <form className="p-4 space-y-4">
      <div>
        <label>Part Number</label>
        <input type="text" value={data.part_number || ''} onChange={(e) => handleChange('part_number', e.target.value)} />
      </div>
      <div>
        <label>Description</label>
        <textarea value={data.description || ''} onChange={(e) => handleChange('description', e.target.value)} />
      </div>
    </form>
  );
};

const closeButton: React.CSSProperties = {
  background: 'none',
  border: 'none',
  fontSize: '1.5rem',
  cursor: 'pointer',
};
