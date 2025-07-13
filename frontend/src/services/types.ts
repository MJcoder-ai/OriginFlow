export interface PresignResponse {
  upload_url: string;
  asset_id: string;
}

export interface CompleteRequest {
  asset_id: string;
  filename: string;
  mime: string;
  size: number;
  component_id: string | null;
}

export interface FileAsset {
  id: string;
  filename: string;
  mime: string;
  size: number;
  url: string;
}
