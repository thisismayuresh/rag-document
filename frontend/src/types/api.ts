// Wire-format types matching the FastAPI response models in
// src/document_agent/api/schemas.py.

export interface HealthInfo {
  status: string;
  chat_provider: string;
  chat_model: string;
  embedding_provider: string;
  embedding_model: string;
  max_documents_per_session: number;
  max_upload_mb: number;
}

export interface DocumentInfo {
  name: string;
  chunk_count: number;
  page_count: number;
  size_bytes: number;
}

export interface SessionInfo {
  session_id: string;
  created_at: string;
  max_documents: number;
  documents: DocumentInfo[];
}

export interface SessionCreated {
  session_id: string;
  created_at: string;
  max_documents: number;
}

export interface DocumentUploaded {
  document: DocumentInfo;
  session: SessionInfo;
}

export interface ChatResponse {
  answer: string;
}

export interface ErrorPayload {
  error: {
    code: string;
    message: string;
  };
}
