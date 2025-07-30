import React from 'react';
import { useAppStore } from '../appStore';

const LayerSelector: React.FC = () => {
  const layers = useAppStore((s) => s.layers);
  const currentLayer = useAppStore((s) => s.currentLayer);
  const setCurrentLayer = useAppStore((s) => s.setCurrentLayer);

  return (
    <div className="flex space-x-2 mb-2" aria-label="Layer selector">
      {layers.map((layer) => (
        <button
          key={layer}
          onClick={() => setCurrentLayer(layer)}
          className={
            'px-3 py-1 rounded-md text-sm ' +
            (currentLayer === layer
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200')
          }
        >
          {layer}
        </button>
      ))}
    </div>
  );
};

export default LayerSelector;
