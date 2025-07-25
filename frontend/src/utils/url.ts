export function makeAbsoluteUrl(relativePath: string, apiBaseUrl: string): string {
  const backendBase = apiBaseUrl.replace('/api/v1', '');
  if (relativePath.startsWith('/')) {
    return `${backendBase}${relativePath}`;
  }
  return `${backendBase}/${relativePath}`;
}
