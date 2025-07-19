import { FileAsset } from './types';
import { API_BASE_URL } from './api';

export async function uploadFile(
  file: File,
  onProg: (p: number) => void,
): Promise<FileAsset> {
  return new Promise((res, rej) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProg(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        res(JSON.parse(xhr.responseText));
      } else {
        rej(xhr);
      }
    };
    xhr.onerror = () => rej(xhr);

    xhr.open('POST', `${API_BASE_URL}/files/upload`);
    xhr.send(formData);
  });
}

export async function listFiles(): Promise<FileAsset[]> {
  const resp = await fetch(`${API_BASE_URL}/files/`);
  if (!resp.ok) throw new Error('Failed to fetch files');
  return resp.json();
}
