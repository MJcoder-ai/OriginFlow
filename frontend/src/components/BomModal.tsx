import React from 'react';

export const BomModal: React.FC<{ items: string[]; onClose: () => void }> = ({ items, onClose }) => (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
    <div className="bg-white p-4 rounded">
      <h2 className="font-bold mb-2">Bill of Materials</h2>
      <ul className="list-disc pl-6 max-h-60 overflow-auto">
        {items.map((it) => (
          <li key={it}>{it}</li>
        ))}
      </ul>
      <button className="mt-4 btn" onClick={onClose}>
        Close
      </button>
    </div>
  </div>
);
