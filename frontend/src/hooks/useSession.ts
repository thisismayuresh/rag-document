// Session lifecycle: create, list/upload/remove documents, reset.
//
// The hook owns the session state; the component destructures only the
// functions and flags it needs. Every API call is wrapped in try/catch and
// surfaces a user-readable `error` string.

import { useCallback, useEffect, useRef, useState } from "react";

import { isAbortError, toErrorMessages } from "../lib/errors";
import {
  createSession,
  deleteSession,
  removeDocument,
  uploadDocument,
} from "../lib/http";
import type { SessionCreated, SessionInfo } from "../types/api";

export interface UseSessionResult {
  session: SessionInfo | null;
  isStarting: boolean;
  isUploading: boolean;
  isRemoving: boolean;
  error: string | null;
  startSession: () => Promise<SessionCreated | null>;
  upload: (file: File) => Promise<boolean>;
  remove: (documentName: string) => Promise<boolean>;
  resetSession: () => Promise<void>;
  clearError: () => void;
}

export function useSession(): UseSessionResult {
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  const startSession = useCallback(async (): Promise<SessionCreated | null> => {
    setIsStarting(true);
    setError(null);
    try {
      const created = await createSession();
      setSession({
        session_id: created.session_id,
        created_at: created.created_at,
        max_documents: created.max_documents,
        documents: [],
      });
      return created;
    } catch (caught) {
      if (!isAbortError(caught)) {
        setError(toErrorMessages(caught));
      }
      return null;
    } finally {
      setIsStarting(false);
    }
  }, []);

  const upload = useCallback(
    async (file: File): Promise<boolean> => {
      if (!session) {
        setError("Start a session before uploading documents.");
        return false;
      }

      const controller = new AbortController();
      abortRef.current = controller;
      setIsUploading(true);
      setError(null);
      try {
        const uploaded = await uploadDocument(session.session_id, file, controller.signal);
        setSession(uploaded.session);
        return true;
      } catch (caught) {
        if (!isAbortError(caught)) {
          setError(toErrorMessages(caught));
        }
        return false;
      } finally {
        setIsUploading(false);
        abortRef.current = null;
      }
    },
    [session],
  );

  const remove = useCallback(
    async (documentName: string): Promise<boolean> => {
      if (!session) {
        return false;
      }

      const controller = new AbortController();
      abortRef.current = controller;
      setIsRemoving(true);
      setError(null);
      try {
        await removeDocument(session.session_id, documentName, controller.signal);
        setSession((current) =>
          current === null
            ? null
            : {
                ...current,
                documents: current.documents.filter((doc) => doc.name !== documentName),
              },
        );
        return true;
      } catch (caught) {
        if (!isAbortError(caught)) {
          setError(toErrorMessages(caught));
        }
        return false;
      } finally {
        setIsRemoving(false);
        abortRef.current = null;
      }
    },
    [session],
  );

  const resetSession = useCallback(async (): Promise<void> => {
    const previous = session;
    setSession(null);
    if (previous) {
      // Best-effort cleanup of the old session's vectors; a fresh session
      // matters more than waiting on the delete.
      try {
        await deleteSession(previous.session_id);
      } catch (caught) {
        if (!isAbortError(caught)) {
          console.warn("Could not delete previous session", caught);
        }
      }
    }
    await startSession();
  }, [session, startSession]);

  const clearError = useCallback(() => setError(null), []);

  return {
    session,
    isStarting,
    isUploading,
    isRemoving,
    error,
    startSession,
    upload,
    remove,
    resetSession,
    clearError,
  };
}
