// The one place the frontend talks to the backend. Every call goes through
// here so error handling, abort support, and the response contract only
// exist once. No request timeouts: the backend may take minutes to answer,
// and AbortController is the only way out.

import { API_BASE, endpoints } from "../constants/api";
import type {
  ChatResponse,
  DocumentUploaded,
  ErrorPayload,
  HealthInfo,
  SessionCreated,
  SessionInfo,
} from "../types/api";
import { ApiError, isAbortError } from "./errors";

interface RequestOptions {
  method?: "GET" | "POST" | "DELETE";
  jsonBody?: unknown;
  signal?: AbortSignal;
}

export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", jsonBody, signal } = options;

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers:
        jsonBody === undefined
          ? undefined
          : { "Content-Type": "application/json" },
      body: jsonBody === undefined ? undefined : JSON.stringify(jsonBody),
      signal,
    });
    return await readBody<T>(response);
  } catch (error) {
    throw normalizeError(error);
  }
}

export function fetchHealth(signal?: AbortSignal): Promise<HealthInfo> {
  return request<HealthInfo>(endpoints.health, { signal });
}

export function createSession(signal?: AbortSignal): Promise<SessionCreated> {
  return request<SessionCreated>(endpoints.sessions, {
    method: "POST",
    signal,
  });
}

export function fetchSession(
  sessionId: string,
  signal?: AbortSignal,
): Promise<SessionInfo> {
  return request<SessionInfo>(endpoints.session(sessionId), { signal });
}

export function deleteSession(
  sessionId: string,
  signal?: AbortSignal,
): Promise<void> {
  return request<void>(endpoints.session(sessionId), {
    method: "DELETE",
    signal,
  });
}

export function uploadDocument(
  sessionId: string,
  file: File,
  signal?: AbortSignal,
): Promise<DocumentUploaded> {
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("file", file);

  // No Content-Type here: the browser must add the multipart boundary itself.
  return sendMultipart(endpoints.documents, formData, signal);
}

export function removeDocument(
  sessionId: string,
  documentName: string,
  signal?: AbortSignal,
): Promise<void> {
  return request<void>(endpoints.sessionDocument(sessionId, documentName), {
    method: "DELETE",
    signal,
  });
}

export function sendChatMessage(
  sessionId: string,
  message: string,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  return request<ChatResponse>(endpoints.chat, {
    method: "POST",
    jsonBody: { session_id: sessionId, message },
    signal,
  });
}

async function sendMultipart<T>(
  path: string,
  formData: FormData,
  signal?: AbortSignal,
): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      body: formData,
      signal,
    });
    return await readBody<T>(response);
  } catch (error) {
    throw normalizeError(error);
  }
}

async function readBody<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const payload: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw errorFromPayload(response.status, payload);
  }

  return payload as T;
}

function errorFromPayload(status: number, payload: unknown): ApiError {
  const errorPayload = payload as ErrorPayload | null;
  const message =
    errorPayload?.error?.message ?? `Request failed with status ${status}.`;
  const code = errorPayload?.error?.code ?? "request_failed";
  return new ApiError(status, code, message);
}

function normalizeError(error: unknown): unknown {
  if (error instanceof ApiError || isAbortError(error)) {
    return error;
  }
  if (error instanceof TypeError) {
    // fetch rejects with TypeError when the network itself fails.
    return new ApiError(
      0,
      "network_error",
      "Cannot reach the server. Is the backend running?",
    );
  }
  return error;
}
