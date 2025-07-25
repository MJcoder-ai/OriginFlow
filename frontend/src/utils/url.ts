/**
 * Convert a relative backend path to an absolute URL.
 *
 * PDF datasheets now stream via `/files/{id}/file`, so this helper is mainly
 * used for image or static asset links.
 */
export function makeAbsoluteUrl(relativePath: string, apiBaseUrl: string): string {
  const backendBase = apiBaseUrl.replace('/api/v1', '');
  if (relativePath.startsWith('/')) {
    return `${backendBase}${relativePath}`;
  }
  return `${backendBase}/${relativePath}`;
}
