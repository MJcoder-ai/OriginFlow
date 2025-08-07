import { useAppStore, UploadEntry } from '../appStore';
import clsx from 'clsx';
import { useDraggable } from '@dnd-kit/core';
import { getFileStatus, parseDatasheet } from '../services/fileApi';
import { API_BASE_URL } from '../config';
import React, { useState } from 'react';
import { Search, Filter } from 'lucide-react';

const FileEntry: React.FC<{ u: UploadEntry }> = ({ u }) => {
  const setActiveDatasheet = useAppStore((s) => s.setActiveDatasheet);
  const setRoute = useAppStore((s) => s.setRoute);
  const updateUpload = useAppStore((s) => s.updateUpload);
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `file-asset-${u.id}`,
    data: { type: 'file-asset', asset: u },
  });

  const StatusIndicator = () => {
    if (u.parsing_status === 'processing') {
      return <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500" />;
    }
    if (u.parsing_status === 'failed') {
      return (
        <span title={u.parsing_error || 'An unknown error occurred.'} className="text-red-500">
          ❗
        </span>
      );
    }
    if (u.parsing_status === 'success') {
      return <span className="text-green-500">✔</span>;
    }
    return null;
  };

  const handleParse = async () => {
    try {
        updateUpload(u.id, { parsing_status: 'processing' });
        await parseDatasheet(u.id);

        const poll = setInterval(async () => {
            try {
                const updatedAsset = await getFileStatus(u.id);
                if (updatedAsset.parsing_status === 'success') {
                    clearInterval(poll);
                    updateUpload(u.id, { parsing_status: 'success', parsing_error: null });
                    const fileUrl = `${API_BASE_URL}/files/${updatedAsset.id}/file`;
                    setActiveDatasheet({ id: updatedAsset.id, url: fileUrl, payload: updatedAsset.parsed_payload });
                    setRoute('components');
                } else if (updatedAsset.parsing_status === 'failed') {
                    clearInterval(poll);
                    updateUpload(u.id, { parsing_status: 'failed', parsing_error: updatedAsset.parsing_error });
                }
            } catch (err: any) {
                clearInterval(poll);
                updateUpload(u.id, { parsing_status: 'failed', parsing_error: err.message || 'Failed to fetch status' });
            }
        }, 2000);
    } catch (err: any) {
      console.error(err);
      updateUpload(u.id, {
        parsing_status: 'failed',
        parsing_error: err.message || 'Failed to parse datasheet',
      });
    }
  };
  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      onClick={async () => {
        if (u.parsing_status === 'success') {
          const asset = await getFileStatus(u.id);
          const fileUrl = `${API_BASE_URL}/files/${asset.id}/file`;
          setActiveDatasheet({ id: asset.id, url: fileUrl, payload: asset.parsed_payload });
          setRoute('components');
        }
      }}
      className={clsx(
        'border rounded p-2 text-sm transition bg-white shadow-sm',
        isDragging && 'opacity-50',
      )}
    >
      <div className="flex justify-between items-center gap-2">
        <div className="font-medium truncate flex-1">{u.name}</div>
        {(!u.parsing_status || u.parsing_status === 'failed') && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              void handleParse();
            }}
            className="text-xs text-blue-600 hover:underline"
            title="Parse datasheet"
          >
            Parse
          </button>
        )}
      </div>
      <div className="h-1 bg-gray-200 rounded mt-1">
        <div
          className={clsx(
            'h-1 rounded bg-emerald-500 transition-all',
            u.progress > 100 ? 'w-full' : undefined,
          )}
          style={{ width: `${Math.min(u.progress, 100)}%` }}
        />
      </div>
      <div className="text-xs text-right text-gray-500 flex items-center gap-1 mt-1">
        {u.progress > 100 ? <StatusIndicator /> : `${u.progress}%`}
      </div>
    </div>
  );
};

export const FileStagingArea = () => {
  const uploads = useAppStore((s) => s.uploads.filter((u) => u.progress > 100));
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilter, setShowFilter] = useState(false);
  if (!uploads.length) return null;

  // Filter uploads based on search query.  Matches on name or parsed_payload contents.
  const filteredUploads = uploads.filter((u) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    if (u.name && u.name.toLowerCase().includes(query)) return true;
    try {
      if (u.parsed_payload && JSON.stringify(u.parsed_payload).toLowerCase().includes(query)) return true;
    } catch (err) {
      /* ignore JSON stringify errors */
    }
    return false;
  });

  return (
    <div className="p-2 space-y-2">
      <div className="flex items-center gap-2">
        {/* Hide the label when searching to maximise available width */}
        {!showSearch && (
          <div className="text-sm font-medium text-gray-500 px-2 whitespace-nowrap">
            Component Library
          </div>
        )}
        {/* Search input grows to fill the remaining width of the sidebar */}
        {showSearch && (
          <input
            type="text"
            className="flex-grow border rounded-full text-sm px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 transition"
            placeholder="Search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        )}
        {/* Icons remain aligned at the end */}
        <Search
          className="h-5 w-5 cursor-pointer text-gray-500 hover:text-gray-700"
          onClick={() => setShowSearch((prev) => !prev)}
        />
        <Filter
          className="h-5 w-5 cursor-pointer text-gray-500 hover:text-gray-700"
          onClick={() => setShowFilter((prev) => !prev)}
        />
      </div>
      {/* Filter placeholder panel */}
      {showFilter && (
        <div className="px-2 py-1 text-xs text-gray-400 italic bg-gray-50 rounded">
          Advanced filtering options coming soon.
        </div>
      )}
      {filteredUploads.map((u) => (
        <FileEntry key={u.id} u={u} />
      ))}
    </div>
  );
};
