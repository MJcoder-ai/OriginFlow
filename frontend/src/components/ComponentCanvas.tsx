import React from 'react';
import { useDroppable } from '@dnd-kit/core';

/** Canvas used for parsing new components from uploaded datasheets. */
const ComponentCanvas = () => {
  // Register this canvas as a drop target for dnd-kit
  const { setNodeRef } = useDroppable({ id: 'component-canvas' });

  return (
    <div
      ref={setNodeRef}
      className="[grid-area:workspace] flex items-center justify-center text-gray-500 border-2 border-dashed rounded-lg bg-gray-50"
    >
      Drag a datasheet from the library here to parse it.
    </div>
  );
};

export default ComponentCanvas;
