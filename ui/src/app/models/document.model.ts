export interface Document {
  id: string; // Use 'id' to match the backend API response
  _id: string; // Keep _id for any direct MongoDB interactions if necessary
  filename: string;
  content_type: string;
  file_id: string;
  status: string;
  category?: string;
  kvps?: any; // key-value pairs
  text?: string;
  embedding?: any;
  created_at: string;
  processed_at?: string;
  deleted_at?: string;
  _version?: number;
  categorization_explanation?: string;
  processing_chain_id?: string;
  status_message?: string;
}
