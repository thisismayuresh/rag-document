// All API endpoint paths live here. Components and hooks never inline a raw
// path string - if the backend route changes, it changes in exactly one place.
//
// With the Vite dev server the proxy forwards these to FastAPI, so the base
// is empty by default. Set VITE_API_BASE_URL to point elsewhere (e.g. when
// serving the built frontend from another origin without a proxy).

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export const endpoints = {
  health: "/health",
  sessions: "/sessions",
  session: (sessionId: string) => `/sessions/${sessionId}`,
  sessionDocuments: (sessionId: string) => `/sessions/${sessionId}/documents`,
  sessionDocument: (sessionId: string, documentName: string) =>
    `/sessions/${sessionId}/documents/${encodeURIComponent(documentName)}`,
  documents: "/documents",
  chat: "/chat",
} as const;

// Fallback only; the real limit comes from GET /health so the UI and the
// backend can never disagree. Keep in sync with MAX_UPLOAD_MB in .env.
export const DEFAULT_MAX_UPLOAD_MB = 2;
