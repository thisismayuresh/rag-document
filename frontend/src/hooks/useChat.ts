// Chat state for one session: message list, send, stop.
//
// Each send gets its own AbortController. The Stop button aborts the in-
// flight request; unmount aborts too. Aborted requests are not errors -
// they just stop. There are no timeouts: the backend waits as long as the
// LLM needs, and stopping is the user's decision.

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, isAbortError, toErrorMessages } from "../lib/errors";
import { sendChatMessage } from "../lib/http";

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
}

export interface UseChatResult {
  messages: ChatMessage[];
  isWaiting: boolean;
  error: string | null;
  lastErrorCode: string | null;
  send: (text: string) => Promise<void>;
  stop: () => void;
  reset: () => void;
  clearError: () => void;
}

export function useChat(sessionId: string | null): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isWaiting, setIsWaiting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastErrorCode, setLastErrorCode] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const nextIdRef = useRef(0);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  const send = useCallback(
    async (text: string): Promise<void> => {
      if (!sessionId || isWaiting) {
        return;
      }

      const controller = new AbortController();
      abortRef.current = controller;
      const userMessage = { id: nextIdRef.current++, role: "user" as const, content: text };
      setMessages((current) => [...current, userMessage]);
      setIsWaiting(true);
      setError(null);
      setLastErrorCode(null);

      try {
        const response = await sendChatMessage(sessionId, text, controller.signal);
        const assistantMessage = {
          id: nextIdRef.current++,
          role: "assistant" as const,
          content: response.answer,
        };
        setMessages((current) => [...current, assistantMessage]);
      } catch (caught) {
        if (isAbortError(caught)) {
          return;
        }
        setError(toErrorMessages(caught));
        setLastErrorCode(caught instanceof ApiError ? caught.code : null);
      } finally {
        setIsWaiting(false);
        abortRef.current = null;
      }
    },
    [sessionId, isWaiting],
  );

  const stop = useCallback((): void => {
    abortRef.current?.abort();
  }, []);

  const reset = useCallback((): void => {
    setMessages([]);
    setError(null);
    setLastErrorCode(null);
  }, []);

  const clearError = useCallback((): void => {
    setError(null);
    setLastErrorCode(null);
  }, []);

  return { messages, isWaiting, error, lastErrorCode, send, stop, reset, clearError };
}
