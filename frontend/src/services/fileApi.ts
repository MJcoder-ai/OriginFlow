import { FileAsset } from './types';
import { API_BASE_URL } from '../config';

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

/**
 * Triggers the parsing of a previously uploaded datasheet.
 * @param id The ID of the file asset to parse.
 * @returns The file asset with its parsed payload.
 */
export async function parseDatasheet(id: string): Promise<FileAsset> {
  const res = await fetch(`${API_BASE_URL}/files/${id}/parse`, { method: 'POST' });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to parse datasheet');
  }
  return res.json();
}

export async function getFileStatus(id: string): Promise<FileAsset> {
  const res = await fetch(`${API_BASE_URL}/files/${id}`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to fetch status');
  }
  return res.json();
}

export async function updateParsedData(
  id: string,
  payload: any,
  isHumanVerified?: boolean,
): Promise<FileAsset> {
  const body: any = { parsed_payload: payload };
  // Include the is_human_verified flag only when explicitly provided.
  if (typeof isHumanVerified === 'boolean') {
    body.is_human_verified = isHumanVerified;
  }
  const res = await fetch(`${API_BASE_URL}/files/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to save datasheet');
  }
  return res.json();
}
