export interface FileAsset {
  id: string;
  filename: string;
  mime: string;
  size: number;
  url: string;
  parent_asset_id?: string | null;
  uploaded_at: string;
  parsed_payload?: any | null;
  parsed_at: string | null;
  parsing_status?: 'pending' | 'processing' | 'success' | 'failed' | null;
  parsing_error?: string | null;
  is_human_verified?: boolean;

  // Fields present when the asset represents an image.  These may be undefined
  // on non-image assets.  When defined, they help the UI render the
  // thumbnail gallery and allow the user to choose a primary image.
  is_extracted?: boolean;
  is_primary?: boolean;
  width?: number | null;
  height?: number | null;
}
