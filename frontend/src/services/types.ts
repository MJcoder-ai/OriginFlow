export interface FileAsset {
  id: string;
  filename: string;
  mime: string;
  size: number;
  url: string;
  uploaded_at: string;
  parsed_payload?: any | null;
  parsed_at: string | null;
}
