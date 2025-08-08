import { API_BASE_URL } from '../config';

export type SourceRef = { file_id: string; page?: number; bbox?: number[] };
export type ValueVersion = {
  value_id?: string; value: any; unit?: string;
  version?: number; is_verified: boolean; confidence?: number; source?: SourceRef;
};
export type AttributeViewItem = {
  attribute_id: string; display_label: string; key: string;
  category?: string; data_type: 'string'|'number'|'integer'|'boolean'|'enum'|'date'|'json';
  cardinality: 'one'|'many'; unit_default?: string; applicable: boolean;
  current?: ValueVersion; candidates: ValueVersion[]; history_count: number;
};

export type AttributePatch = {
  attribute_id: string; op: 'upsert'|'delete'|'verify';
  value?: any; unit?: string; mark_verified?: boolean;
  group_id?: string; rank?: number; source_id?: string;
};

export async function getAttributesView(componentId: string): Promise<AttributeViewItem[]> {
  const r = await fetch(`${API_BASE_URL}/components/${componentId}/attributes/view`);
  if (!r.ok) throw new Error(`Failed to load attributes: ${r.status}`);
  return r.json();
}

export async function patchAttributes(componentId: string, patches: AttributePatch[]): Promise<void> {
  const r = await fetch(`${API_BASE_URL}/components/${componentId}/attributes`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patches),
  });
  if (!r.ok) throw new Error(`Failed to save: ${r.status}`);
}

export async function confirmClose(componentId: string): Promise<void> {
  const r = await fetch(`${API_BASE_URL}/components/${componentId}/confirm-close`, { method: 'POST' });
  if (!r.ok) throw new Error(`Failed to confirm & close: ${r.status}`);
}

export async function reanalyze(componentId: string): Promise<{ job_id: string }> {
  const r = await fetch(`${API_BASE_URL}/components/${componentId}/reanalyze`, { method: 'POST' });
  if (!r.ok) throw new Error(`Failed to reanalyze: ${r.status}`);
  return r.json();
}
