import React, { useState, useEffect } from 'react';
import { Document, Page } from 'react-pdf';
import { listImages, uploadImages, deleteImage, setPrimaryImage } from '../services/fileApi';
import { API_BASE_URL } from '../config';

interface DatasheetSplitViewProps {
  assetId: string;
  pdfUrl: string;
  initialParsedData: any;
  onSave: (assetId: string, updatedData: any) => void;
  onConfirm: (assetId: string, updatedData: any) => void;
  onAnalyze: (assetId: string) => void;
  onClose: () => void;
}

const DatasheetSplitView: React.FC<DatasheetSplitViewProps> = ({
  assetId,
  pdfUrl,
  initialParsedData,
  onSave,
  onConfirm,
  onAnalyze,
  onClose,
}) => {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [parsedData, setParsedData] = useState(initialParsedData);
  const [isDirty, setIsDirty] = useState(false);
  // Images extracted or uploaded for this asset
  const [images, setImages] = useState<any[]>([]);

  // Fetch existing images on mount or when asset changes
  useEffect(() => {
    async function fetchImages() {
      try {
        const imgs = await listImages(assetId);
        setImages(imgs);
      } catch (err) {
        console.error('Failed to load images', err);
      }
    }
    fetchImages();
  }, [assetId]);

  // Upload handler for new images
  const handleUploadImages = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const list: File[] = [];
    for (let i = 0; i < files.length; i++) {
      list.push(files[i]);
    }
    try {
      const saved = await uploadImages(assetId, list);
      // Append new images to local state
      setImages((prev) => [...prev, ...saved]);
    } catch (err) {
      console.error('Image upload failed', err);
    }
    // Reset input value so the same file can be uploaded again if needed
    e.target.value = '';
  };

  // Delete an image
  const handleDeleteImage = async (imageId: string) => {
    if (!window.confirm('Are you sure you want to delete this image?')) return;
    try {
      await deleteImage(assetId, imageId);
      setImages((prev) => prev.filter((img) => img.id !== imageId));
    } catch (err) {
      console.error('Failed to delete image', err);
    }
  };

  // Set primary image
  const handleSetPrimary = async (imageId: string) => {
    try {
      await setPrimaryImage(assetId, imageId);
      setImages((prev) =>
        prev.map((img) => ({ ...img, is_primary: img.id === imageId }))
      );
    } catch (err) {
      console.error('Failed to set primary image', err);
    }
  };

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

  const handleDataChange = (field: string, value: any) => {
    setParsedData((prev: any) => ({ ...prev, [field]: value }));
    setIsDirty(true);
  };

  const handleSave = () => {
    // Persist the current edits without marking the file as confirmed.
    // Reset the dirty flag so the user won’t be prompted unnecessarily.
    onSave(assetId, parsedData);
    setIsDirty(false);
  };

  const handleAnalyze = () => {
    // If there are unsaved edits, prompt the user before discarding.  If
    // the user chooses Cancel, bail out.
    if (isDirty) {
      const proceed = window.confirm(
        'You have unsaved changes. Re-analysing will discard your edits. Do you want to continue?'
      );
      if (!proceed) return;
    }
    onAnalyze(assetId);
  };

  const handleConfirmAndClose = () => {
    // Persist the current edits and mark them as human verified.  Once
    // saved, clear the dirty flag and close the editor.
    onConfirm(assetId, parsedData);
    setIsDirty(false);
    onClose();
  };

  const handleClose = () => {
    if (isDirty) {
      const proceed = window.confirm(
        'You have unsaved changes. Close without saving?'
      );
      if (!proceed) return;
    }
    onClose();
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
              error={
                <p className="p-4 text-center text-red-500">
                  Failed to load PDF. Please check the file URL and ensure the backend is running.
                </p>
              }
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

      {/* Right Pane: Editable Form */}
      <div className="w-1/2 h-full flex flex-col overflow-y-auto bg-white">
        <div className="p-4 flex justify-between items-center border-b">
          <h2 className="text-lg font-semibold">Review & Confirm</h2>
          <button
            onClick={handleClose}
            className="p-2 rounded-full hover:bg-gray-200"
            aria-label="Close"
          >
            &times;
          </button>
        </div>
        <div className="p-4 flex-grow space-y-4">
          {Object.entries(parsedData).map(([key, value]) => (
            <div key={key}>
              <label className="block text-sm font-medium text-gray-700 capitalize">
                {key.replace(/_/g, ' ')}
              </label>
              {/* Render objects as JSON in a textarea; render primitives in an input. */}
              {typeof value === 'object' && value !== null ? (
                <textarea
                  value={JSON.stringify(value, null, 2)}
                  onChange={(e) => {
                    try {
                      const parsed = JSON.parse(e.target.value);
                      handleDataChange(key, parsed);
                    } catch {
                      handleDataChange(key, e.target.value);
                    }
                  }}
                  rows={4}
                  className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm font-mono"
                />
              ) : (
                <input
                  type="text"
                  value={String(value ?? '')}
                  onChange={(e) => handleDataChange(key, e.target.value)}
                  className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              )}
            </div>
          ))}

          {/* Images Section */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Images</label>
            <div className="flex flex-wrap gap-3">
              {images.map((img) => (
                <div key={img.id} className="relative border rounded p-2">
                  <img
                    src={`${API_BASE_URL}${img.url}`}
                    alt={img.filename}
                    className="w-24 h-24 object-cover rounded"
                  />
                  {img.is_primary && (
                    <span className="absolute top-1 left-1 bg-blue-500 text-white text-xs px-1 py-0.5 rounded">
                      Primary
                    </span>
                  )}
                  <div className="mt-1 flex space-x-1">
                    {!img.is_primary && (
                      <button
                        onClick={() => handleSetPrimary(img.id)}
                        className="text-xs text-blue-600 underline"
                      >
                        Make Default
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteImage(img.id)}
                      className="text-xs text-red-600 underline"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
              {/* Upload Button */}
              <label className="flex items-center justify-center w-24 h-24 border-2 border-dashed rounded cursor-pointer text-gray-500">
                <span className="text-sm">+ Add</span>
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={handleUploadImages}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        </div>
        <div className="p-4 border-t bg-gray-50 flex justify-end space-x-3">
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md shadow-sm hover:bg-green-700 focus:outline-none"
          >
            Save
          </button>
          <button
            onClick={handleConfirmAndClose}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none"
          >
            Confirm & Close
          </button>
          <button
            onClick={handleAnalyze}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none"
          >
            Re-Analyze
          </button>
        </div>
      </div>
    </div>
  );
};

export { DatasheetSplitView };
