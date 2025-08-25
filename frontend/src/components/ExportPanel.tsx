import React from 'react';
import { downloadBOM, downloadSchedules, downloadPackage } from '../services/api';

export default function ExportPanel({ sessionId }: { sessionId: string }) {
  return (
    <div className="export-panel">
      <div className="subhead">Export</div>
      <div className="row">
        <button onClick={()=>downloadBOM(sessionId)}>BOM CSV</button>
        <button onClick={()=>downloadSchedules(sessionId)}>Schedules CSV</button>
        <button onClick={()=>downloadPackage(sessionId)}>Package ZIP</button>
      </div>
    </div>
  );
}