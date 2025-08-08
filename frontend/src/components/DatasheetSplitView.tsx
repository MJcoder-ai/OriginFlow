import React, { useState, useEffect } from 'react';
import { Document, Page } from 'react-pdf';
import { listImages, uploadImages, deleteImage, setPrimaryImage } from '../services/fileApi';
import { confirmClose } from '../services/attributesApi';
import AttributesReviewPanel from './AttributesReviewPanel';
import { API_BASE_URL } from '../config';
import { Star, Trash2, ZoomIn, ZoomOut, ChevronLeft, ChevronRight } from 'lucide-react';

interface DatasheetSplitViewProps {
  assetId: string;
  pdfUrl: string;
  /**
   * Parsed payload returned from the backend. Used as a fallback if the
   * attribute view API does not return any rows. May be null.
   */
  initialParsedData?: any;
  onClose: () => void;
}

const DatasheetSplitView: React.FC<DatasheetSplitViewProps> = ({
  assetId,
  pdfUrl,
  initialParsedData,
  onClose,
}) => {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [images, setImages] = useState<any[]>([]);

  // Track whether any attributes are returned from the backend.
  const [hasAttributes, setHasAttributes] = useState<boolean | null>(null);
  // Track whether the user has unsaved changes
  const [dirty, setDirty] = useState(false);

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

  // Determine if the attributes API returns any rows.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { getAttributesView } = await import('../services/attributesApi');
        const rows = await getAttributesView(assetId);
        if (!cancelled) {
          setHasAttributes(rows && rows.length > 0);
        }
      } catch (err) {
        console.error('Failed to load attributes for preview', err);
        if (!cancelled) setHasAttributes(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [assetId]);

  const handleUploadImages = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const list: File[] = [];
    for (let i = 0; i < files.length; i++) {
      list.push(files[i]);
    }
    try {
      const saved = await uploadImages(assetId, list);
      setImages((prev) => [...prev, ...saved]);
    } catch (err) {
      console.error('Image upload failed', err);
    }
    e.target.value = '';
  };

  const handleDeleteImage = async (imageId: string) => {
    if (!window.confirm('Are you sure you want to delete this image?')) return;
    try {
      await deleteImage(assetId, imageId);
      setImages((prev) => prev.filter((img) => img.id !== imageId));
    } catch (err) {
      console.error('Failed to delete image', err);
    }
  };

  const handleSetPrimary = async (imageId: string) => {
    try {
      await setPrimaryImage(assetId, imageId);
      setImages((prev) => prev.map((img) => ({ ...img, is_primary: img.id === imageId })));
    } catch (err) {
      console.error('Failed to set primary image', err);
    }
  };

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
    setPageNumber(1);
  }

  const goToPrevPage = () => setPageNumber((p) => Math.max(p - 1, 1));
  const goToNextPage = () => setPageNumber((p) => Math.min(p + 1, numPages || 1));
  const zoomIn = () => setScale((s) => s + 0.1);
  const zoomOut = () => setScale((s) => Math.max(s - 0.1, 0.1));

  const handleConfirm = async () => {
    try {
      await confirmClose(assetId);
      onClose();
    } catch (err) {
      console.error('Failed to confirm datasheet', err);
      onClose();
    }
  };

  return (
    <div className="flex h-full min-h-0">
      <div className="w-1/2 border-r flex flex-col min-h-0">
        <div className="flex items-center justify-between p-2 border-b bg-white">
          <div className="flex items-center gap-2">
            <button onClick={goToPrevPage} className="p-1 border rounded"><ChevronLeft className="w-4 h-4" /></button>
            <span className="text-sm">Page {pageNumber} / {numPages}</span>
            <button onClick={goToNextPage} className="p-1 border rounded"><ChevronRight className="w-4 h-4" /></button>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={zoomOut} className="p-1 border rounded"><ZoomOut className="w-4 h-4" /></button>
            <button onClick={zoomIn} className="p-1 border rounded"><ZoomIn className="w-4 h-4" /></button>
          </div>
        </div>
        <div className="flex-1 overflow-auto scroll-container bg-gray-50 flex justify-center min-h-0">
          <Document file={pdfUrl} onLoadSuccess={onDocumentLoadSuccess} className="m-2">
            <Page pageNumber={pageNumber} scale={scale} />
          </Document>
        </div>
      </div>
      {/* Right pane: attributes and images */}
      <div className="w-1/2 flex flex-col min-h-0">
        <div className="flex-1 overflow-auto scroll-container p-4 flex flex-col gap-4 min-h-0">
          {/* Show the attributes review panel if the API returned rows; otherwise show a fallback view */}
          {hasAttributes === null ? (
            <div className="text-sm text-gray-500">Loading attributes…</div>
          ) : hasAttributes ? (
            <AttributesReviewPanel
              componentId={assetId}
              onDirtyChange={(d) => setDirty(d)}
            />
          ) : initialParsedData ? (
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium text-gray-700 mb-1">Raw data</h3>
              {Object.entries(initialParsedData).map(([key, value]) => (
                <div
                  key={key}
                  className="grid grid-cols-[200px,1fr] items-start gap-3 px-3 py-2 border-b last:border-0"
                >
                  <div className="text-sm font-medium text-gray-700 capitalize">
                    {key.replace(/_/g, ' ')}
                  </div>
                  <div className="text-sm text-gray-800 break-words whitespace-pre-wrap">
                    {typeof value === 'object' && value !== null
                      ? JSON.stringify(value, null, 2)
                      : String(value)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-gray-500">No attributes or parsed data available.</div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Images</label>
            <div className="flex flex-wrap gap-3">
              {images.map((img) => (
                <div key={img.id} className="relative border rounded">
                  <img
                    src={`${API_BASE_URL.replace(/\/api\/v1$/, '')}${img.url}`}
                    alt={img.filename}
                    className="w-24 h-24 object-cover rounded"
                  />
                  {img.is_primary && (
                    <span className="absolute top-1 left-1 bg-blue-500 text-white text-xs px-1 rounded">Primary</span>
                  )}
                  <button
                    onClick={() => handleSetPrimary(img.id)}
                    className="absolute top-1 right-6 text-white"
                    title="Make primary"
                  >
                    <Star className={img.is_primary ? 'w-4 h-4 text-yellow-400 fill-yellow-400' : 'w-4 h-4 text-white drop-shadow'} />
                  </button>
                  <button
                    onClick={() => handleDeleteImage(img.id)}
                    className="absolute top-1 right-1 text-white"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </button>
                </div>
              ))}
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
            onClick={handleConfirm}
            disabled={hasAttributes ? !dirty : false}
            className={`px-4 py-2 text-sm font-medium border border-transparent rounded-md shadow-sm focus:outline-none ${
              hasAttributes && !dirty
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            Confirm & Close
          </button>
        </div>
      </div>
    </div>
  );
};

export { DatasheetSplitView };

