import React, { useState } from 'react';
import { Document, Page } from 'react-pdf';

interface DatasheetSplitViewProps {
  pdfUrl: string;
  // Keep the other props as they are for the right-side form
  initialParsedData: any;
  assetId: string;
  onSave: (assetId: string, updatedData: any) => void;
  onAnalyze: (assetId: string) => void;
}

const DatasheetSplitView: React.FC<DatasheetSplitViewProps> = ({
  pdfUrl,
  initialParsedData,
  assetId,
  onSave,
  onAnalyze,
}) => {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [parsedData, setParsedData] = useState(initialParsedData);

  // Callback function when the document is successfully loaded
  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
    setPageNumber(1); // Reset to first page on new PDF
  }

  // Navigation functions
  const goToPrevPage = () =>
    setPageNumber((prevPage) => Math.max(prevPage - 1, 1));

  const goToNextPage = () =>
    setPageNumber((prevPage) => Math.min(prevPage + 1, numPages || 1));

  // ... (keep your existing handleSave, handleAnalyze, and handleDataChange functions)
  const handleDataChange = (field: string, value: any) => {
    setParsedData((prev: any) => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    onSave(assetId, parsedData);
  };

  const handleAnalyze = () => {
    onAnalyze(assetId);
  };

  return (
    <div className="flex flex-1 w-full h-full">
      {/* Left Pane: PDF Viewer */}
      <div className="w-1/2 h-full border-r border-gray-200 flex flex-col bg-gray-50">
        <div className="flex-grow overflow-y-auto">
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              loading={<p className="p-4 text-center">Loading PDF...</p>}
              error={<p className="p-4 text-center text-red-500">Failed to load PDF.</p>}
            >
              <Page pageNumber={pageNumber} />
            </Document>
        </div>
        {/* Pagination Controls */}
        {numPages && (
            <div className="flex items-center justify-center p-2 border-t bg-white shadow-sm">
                <button
                    onClick={goToPrevPage}
                    disabled={pageNumber <= 1}
                    className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Prev
                </button>
                <p className="text-sm text-gray-700 mx-4">
                    Page {pageNumber} of {numPages}
                </p>
                <button
                    onClick={goToNextPage}
                    disabled={pageNumber >= numPages}
                    className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Next
                </button>
            </div>
        )}
      </div>

      {/* Right Pane: Editable Form (This part remains the same) */}
      <div className="w-1/2 h-full flex flex-col overflow-y-auto">
        <div className="p-4 flex-grow">
          <h2 className="text-lg font-semibold mb-4">Parsed Component Data</h2>
          {/* Your form fields go here, for example: */}
          <div className="space-y-4">
            {Object.entries(parsedData).map(([key, value]) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-700 capitalize">{key.replace(/_/g, ' ')}</label>
                <input
                  type="text"
                  value={String(value)}
                  onChange={(e) => handleDataChange(key, e.target.value)}
                  className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
            ))}
          </div>
        </div>
        <div className="p-4 border-t bg-white flex justify-end space-x-2">
            <button
                onClick={handleAnalyze}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none"
            >
                Analyze
            </button>
            <button
                onClick={handleSave}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md shadow-sm hover:bg-green-700 focus:outline-none"
            >
                Save
            </button>
        </div>
      </div>
    </div>
  );
};

export default DatasheetSplitView;
