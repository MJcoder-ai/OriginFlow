import { getAttributesView } from '../services/attributesApi';

/**
 * Export the current component attributes to a CSV file. The CSV will
 * contain a header row followed by one line per attribute. Only the
 * latest value (current) for each attribute is exported. Units are
 * included in a separate column. Images and other binary fields are
 * omitted.
 *
 * @param componentId The ID of the component whose attributes should be exported.
 */
export async function exportAttributesToCsv(componentId: string): Promise<void> {
  const items = await getAttributesView(componentId);
  const rows: string[][] = [];
  rows.push(['attribute_key', 'label', 'value', 'unit']);
  for (const item of items) {
    const key = item.key;
    const label = item.display_label;
    const value = item.current?.value ?? '';
    const unit = item.current?.unit ?? item.unit_default ?? '';
    const safeValue = String(value).replace(/"/g, '""');
    rows.push([key, label, safeValue, unit]);
  }
  const csvContent = rows
    .map((r) => r.map((cell) => `"${cell}"`).join(','))
    .join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `component_${componentId}_attributes.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

