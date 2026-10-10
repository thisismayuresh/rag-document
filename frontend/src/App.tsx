import { useEffect, useRef, useState } from "react";

import { ChatPanel } from "./components/ChatPanel";
import { ErrorBanner } from "./components/ErrorBanner";
import { Sidebar } from "./components/Sidebar";
import { useChat } from "./hooks/useChat";
import { useSession } from "./hooks/useSession";
import { isAbortError } from "./lib/errors";
import { fetchHealth } from "./lib/http";
import { DEFAULT_MAX_UPLOAD_MB } from "./constants/api";
import type { HealthInfo } from "./types/api";
import "./styles/global.css";

const UNKNOWN_SESSION_CODE = "unknown_session";

export function App() {
  const sessionApi = useSession();
  const chat = useChat(sessionApi.session?.session_id ?? null);
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const hasBootedRef = useRef(false);

  // Boot: load service info, then open a session. Health is informational -
  // if it fails the app still works, it just cannot show model names.
  // The ref keeps React StrictMode's double mount from opening two sessions.
  useEffect(() => {
    if (hasBootedRef.current) {
      return;
    }
    hasBootedRef.current = true;

    const controller = new AbortController();

    async function boot(): Promise<void> {
      try {
        const info = await fetchHealth(controller.signal);
        setHealth(info);
      } catch (caught) {
        if (!isAbortError(caught)) {
          console.warn("Could not load /health", caught);
        }
      }
      await sessionApi.startSession();
    }

    void boot();
    return () => controller.abort();
  }, [sessionApi.startSession]);

  // The backend keeps sessions in memory. If it restarted (or the session
  // aged out), start fresh instead of leaving the user stuck.
  useEffect(() => {
    if (chat.lastErrorCode !== UNKNOWN_SESSION_CODE) {
      return;
    }
    chat.reset();
    void sessionApi.resetSession();
  }, [chat.lastErrorCode, chat.reset, sessionApi.resetSession]);

  const maxUploadMb = health?.max_upload_mb ?? DEFAULT_MAX_UPLOAD_MB;
  const maxUploadBytes = maxUploadMb * 1024 * 1024;

  function handleNewSession(): void {
    chat.reset();
    void sessionApi.resetSession();
  }

  if (sessionApi.isStarting && !sessionApi.session) {
    return (
      <div className="boot-screen">
        <span className="moon-loader" aria-hidden="true" />
        <span>Starting a session...</span>
      </div>
    );
  }

  if (!sessionApi.session && sessionApi.error) {
    return (
      <div className="boot-screen">
        <ErrorBanner message={sessionApi.error} onDismiss={sessionApi.clearError} />
        <button type="button" className="primary-button" onClick={handleNewSession}>
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Local Document Agent</h1>
        <div className="meta">
          <span>Session {sessionApi.session?.session_id.slice(0, 8) ?? "-"}</span>{" "}
          <button type="button" className="ghost-button" onClick={handleNewSession}>
            New session
          </button>
        </div>
      </header>

      <div className="app-body">
        <Sidebar
          session={sessionApi.session}
          health={health}
          maxUploadBytes={maxUploadBytes}
          isUploading={sessionApi.isUploading}
          isRemoving={sessionApi.isRemoving}
          onFileAccepted={(file) => void sessionApi.upload(file)}
          onRemoveDocument={(name) => void sessionApi.remove(name)}
        />

        <ChatPanel
          messages={chat.messages}
          isWaiting={chat.isWaiting}
          error={chat.error ?? sessionApi.error}
          hasSession={sessionApi.session !== null}
          onSend={(text) => void chat.send(text)}
          onStop={chat.stop}
          onDismissError={() => {
            chat.clearError();
            sessionApi.clearError();
          }}
        />
      </div>
    </div>
  );
}
