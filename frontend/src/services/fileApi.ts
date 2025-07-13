import { PresignResponse, CompleteRequest, FileAsset } from './types';
import { API_BASE_URL } from './api';

async function fetchJson<T>(url: string, init: RequestInit) {
  const res = await fetch(url, { ...init, headers: { 'Content-Type': 'application/json' } });
  if (!res.ok) throw new Error(`Request failed ${res.status}`);
  return res.json() as Promise<T>;
}

export async function presign(filename: string, mime: string) {
  return fetchJson<PresignResponse>(`${API_BASE_URL}/files/presign`, {
    method: 'POST',
    body: JSON.stringify({ filename, mime }),
  });
}

export async function complete(body: CompleteRequest) {
  return fetchJson<FileAsset>(`${API_BASE_URL}/files/complete`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function uploadWithProgress(
  url: string,
  file: File,
  onProg: (p: number) => void,
) {
  return new Promise<void>((res, rej) => {
    const xhr = new XMLHttpRequest();
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProg(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => (xhr.status >= 200 && xhr.status < 300 ? res() : rej(xhr));
    xhr.onerror = () => rej(xhr);
    xhr.open('PUT', url);
    xhr.send(file);
  });
}
