import React, { useEffect, useMemo, useState } from 'react';
import { getAttributesView, patchAttributes, AttributeViewItem } from '../services/attributesApi';
import { debounce } from '../utils/debounce';

type Props = {
  componentId: string;
  onDirtyChange?: (dirty: boolean) => void;
};

export default function AttributesReviewPanel({ componentId, onDirtyChange }: Props) {
  const [rows, setRows] = useState<AttributeViewItem[]>([]);
  const [dirtyMap, setDirtyMap] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      const data = await getAttributesView(componentId);
      if (!alive) return;
      setRows(data);
      setDirtyMap({});
      setLoading(false);
      onDirtyChange?.(false);
    })();
    return () => { alive = false; };
  }, [componentId]);

  const setDirty = (attribute_id: string, value: any, unit?: string) => {
    setDirtyMap(m => {
      const next = { ...m, [attribute_id]: { value, unit } };
      onDirtyChange?.(true);
      return next;
    });
    debouncedSave(attribute_id, value, unit);
  };

  const saveOne = async (attribute_id: string, value: any, unit?: string) => {
    await patchAttributes(componentId, [{ attribute_id, op: 'upsert', value, unit }]);
    setDirtyMap(m => {
      const n = { ...m };
      delete n[attribute_id];
      const dirty = Object.keys(n).length > 0;
      onDirtyChange?.(dirty);
      return n;
    });
  };

  const debouncedSave = useMemo(() => debounce(saveOne, 500), [componentId]);

  if (loading) return <div className="p-4 text-sm text-gray-500">Loading attributes…</div>;

  return (
    <div className="flex flex-col gap-4">
      {rows.map((row) => {
        const cur =
          dirtyMap[row.attribute_id]?.value ?? row.current?.value ?? '';
        const unit =
          dirtyMap[row.attribute_id]?.unit ??
          row.current?.unit ??
          row.unit_default ??
          '';
        const editable = row.data_type !== 'json';
        return (
          <div
            key={row.attribute_id}
            className="p-3 border-b last:border-0 hover:bg-gray-50"
          >
            {/* Label + category */}
            <label className="block text-sm font-medium text-gray-600 mb-1">
              {row.display_label}
              {row.category && (
                <span className="ml-2 text-xs text-gray-400">
                  {row.category}
                </span>
              )}
            </label>
            {/* Editor */}
            {editable ? (
              <input
                className="w-full border rounded px-2 py-1 text-sm"
                value={cur as any}
                onChange={(e) =>
                  setDirty(row.attribute_id, e.target.value, unit)
                }
              />
            ) : (
              <textarea
                className="w-full border rounded px-2 py-1 text-sm"
                value={String(cur ?? '')}
                onChange={(e) =>
                  setDirty(row.attribute_id, e.target.value, unit)
                }
                rows={2}
              />
            )}
            {/* Unit and confidence */}
            <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
              <div className="flex gap-2 items-center">
                {unit ? (
                  <span className="px-1.5 py-0.5 rounded bg-gray-100">
                    {unit}
                  </span>
                ) : null}
                {row.current?.confidence != null && (
                  <span className="px-1.5 py-0.5 rounded bg-gray-100">
                    {Math.round((row.current.confidence || 0) * 100)}%
                  </span>
                )}
              </div>
            </div>
            {/* Candidate values */}
            {row.candidates?.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {row.candidates.map((c, i) => (
                  <button
                    key={i}
                    className="text-xs border rounded px-2 py-1 hover:bg-gray-100"
                    onClick={() => setDirty(row.attribute_id, c.value, c.unit)}
                    title={`From page ${c.source?.page ?? '?'}`}
                  >
                    {String(c.value)} {c.unit ?? ''}
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

