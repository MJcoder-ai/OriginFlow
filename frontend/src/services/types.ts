export interface FileAsset {
  id: string;
  filename: string;
  mime: string;
  size: number;
  url: string;
  uploaded_at: string;
  parsed_payload?: any | null;
  parsed_at: string | null;
  parsing_status?: 'pending' | 'processing' | 'success' | 'failed' | null;
  parsing_error?: string | null;
  is_human_verified?: boolean;
}
