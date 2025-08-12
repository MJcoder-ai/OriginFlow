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
        const contentType = xhr.getResponseHeader('Content-Type') || '';
        let detail = `${xhr.status} ${xhr.statusText}`;
        if (contentType.includes('application/json')) {
          try {
            const parsed = JSON.parse(xhr.responseText);
            if (parsed && parsed.detail) detail = `${xhr.status}: ${parsed.detail}`;
          } catch {}
        }
        const err: any = new Error(detail);
        err.status = xhr.status;
        err.responseText = xhr.responseText;
        rej(err);
      }
    };
    xhr.onerror = () => {
      const err: any = new Error('Network error during upload');
      err.status = 0;
      rej(err);
    };

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

/**
 * List all images associated with a given datasheet asset.
 * @param assetId The ID of the parent file asset.
 */
export async function listImages(assetId: string): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/files/${assetId}/images`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to list images');
  }
  return res.json();
}

/**
 * Upload one or more images for a datasheet asset. Accepts a list of File objects.
 * Returns the saved FileAsset objects.
 */
export async function uploadImages(assetId: string, images: File[]): Promise<FileAsset[]> {
  const formData = new FormData();
  images.forEach((file) => {
    formData.append('files', file);
  });
  const res = await fetch(`${API_BASE_URL}/files/${assetId}/images`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to upload images');
  }
  return res.json();
}

/**
 * Delete an image associated with a datasheet.
 */
export async function deleteImage(assetId: string, imageId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/files/${assetId}/images/${imageId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to delete image');
  }
}

/**
 * Set an image as the primary thumbnail for a datasheet.
 */
export async function setPrimaryImage(assetId: string, imageId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/files/${assetId}/images/${imageId}/primary`, {
    method: 'PATCH',
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to set primary image');
  }
}
