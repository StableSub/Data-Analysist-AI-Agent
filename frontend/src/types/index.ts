export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface FileInfo {
  dataset_id: string;
  meta: {
    sniff: {
      filetype: string;
      encoding: string;
      delimiter: string;
      ext: string;
    };
    shape_sample: number[];
    shape_total: number[];
    columns: string[];
    ext: string;
    raw_path: string;
  };
  preview_df: Record<string, any>[];
  dtype_df: {
    column: string;
    null_count: number;
    null_ratio: number;
    dtype: string;
  }[];
}

export interface ChatResponse {
  response: string;
  messages: ChatMessage[];
}

export interface FileUploadResponse {
  success: boolean;
  message: string;
  dataset_id?: string;
  meta?: FileInfo['meta'];
  preview_df?: Record<string, any>[];
  dtype_df?: FileInfo['dtype_df'];
}

