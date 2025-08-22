import React, { useState, useEffect } from 'react';
import { Document, Page } from 'react-pdf';
import { listImages, uploadImages, deleteImage, setPrimaryImage, updateParsedData } from '../services/fileApi';
// Confirm & Close now resides in the toolbar; no direct confirm here.
import { useAppStore } from '../appStore';
import AttributesReviewPanel from './AttributesReviewPanel';
import { API_BASE_URL } from '../config';
import { Star, Trash2, ZoomIn, ZoomOut, ChevronLeft, ChevronRight } from 'lucide-react';
import { debounce } from '../utils/debounce';

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

  // Global dirty flag setter from the app store
  const setDatasheetDirty = useAppStore((s) => s.setDatasheetDirty);

  // Track whether any attributes are returned from the backend.
  const [hasAttributes, setHasAttributes] = useState<boolean | null>(null);

  // When attributes are unavailable we render and edit the raw parsed payload.
  // Maintain a local copy for editing. Start with the provided initialParsedData or an empty object.
  const [parsedData, setParsedData] = useState<any>(initialParsedData || {});

  // When the asset or initialParsedData changes, reset the local parsedData
  useEffect(() => {
    setParsedData(initialParsedData || {});
  }, [assetId, initialParsedData]);

  // Debounced saver for the raw parsed payload. The debounce prevents a request on every keystroke.
  const debouncedSave = React.useMemo(() => {
    return debounce((data: any) => {
      updateParsedData(assetId, data, false).catch((err) => {
        console.error('Failed to save parsed data', err);
      });
    }, 500);
  }, [assetId]);

  // Reset the datasheet dirty flag whenever a new asset is loaded
  useEffect(() => {
    setDatasheetDirty(false);
  }, [assetId]);

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
      // Mark datasheet as dirty when new images are added
      setDatasheetDirty(true);
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
      setDatasheetDirty(true);
    } catch (err) {
      console.error('Failed to delete image', err);
    }
  };

  const handleSetPrimary = async (imageId: string) => {
    try {
      await setPrimaryImage(assetId, imageId);
      setImages((prev) =>
        prev.map((img) => ({ ...img, is_primary: img.id === imageId }))
      );
      setDatasheetDirty(true);
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
              onDirtyChange={(d) => {
                // Propagate dirty state to the global app store
                setDatasheetDirty(d);
              }}
            />
          ) : initialParsedData ? (
            <div className="flex flex-col gap-0">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                Raw data
              </h3>
              {/* Editable fallback form for each key/value in parsedData */}
              {Object.entries(parsedData).map(([key, value]) => (
                <div key={key} className="p-3 border-b last:border-0">
                  <label className="block text-sm font-medium text-gray-600 mb-1 capitalize">
                    {key.replace(/_/g, ' ')}
                  </label>
                    {typeof value === 'object' && value !== null ? (
                      <textarea
                        value={JSON.stringify(value, null, 2)}
                        onChange={(e) => {
                          let newValue: any = e.target.value;
                          try {
                            newValue = JSON.parse(e.target.value);
                          } catch {
                            /* keep as string */
                          }
                          setParsedData((prev: any) => {
                            const updated = { ...prev, [key]: newValue };
                            setDatasheetDirty(true);
                            debouncedSave(updated);
                            return updated;
                          });
                        }}
                        rows={3}
                        className="w-full border rounded px-2 py-1 text-sm font-mono resize-y"
                      />
                    ) : (
                      <input
                        type="text"
                        value={String(value ?? '')}
                        onChange={(e) => {
                          const newValue: any = e.target.value;
                          setParsedData((prev: any) => {
                            const updated = { ...prev, [key]: newValue };
                            setDatasheetDirty(true);
                            debouncedSave(updated);
                            return updated;
                          });
                        }}
                        className="w-full border rounded px-2 py-1 text-sm"
                      />
                    )}
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
        {/* Footer removed — Confirm & Close and Re‑Analyze now live in the toolbar. */}
      </div>
    </div>
  </div>
  );
};

export { DatasheetSplitView };

