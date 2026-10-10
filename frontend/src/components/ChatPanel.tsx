import type { ChatMessage } from "../hooks/useChat";
import { ChatComposer } from "./ChatComposer";
import { ErrorBanner } from "./ErrorBanner";
import { MessageList } from "./MessageList";
import { MoonLoader } from "./MoonLoader";

interface ChatPanelProps {
  messages: ChatMessage[];
  isWaiting: boolean;
  error: string | null;
  hasSession: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
  onDismissError: () => void;
}

export function ChatPanel({
  messages,
  isWaiting,
  error,
  hasSession,
  onSend,
  onStop,
  onDismissError,
}: ChatPanelProps) {
  return (
    <main className="chat-panel">
      {error && (
        <div className="banner-row">
          <ErrorBanner message={error} onDismiss={onDismissError} />
        </div>
      )}

      {messages.length === 0 && !isWaiting ? (
        <div className="chat-placeholder">
          Upload up to five PDFs on the left, then ask questions about them here.
          Answers only come from your documents.
        </div>
      ) : (
        <MessageList messages={messages} />
      )}

      {isWaiting && (
        <div className="waiting-row">
          <MoonLoader />
          <span>Waiting for the model... press Stop to cancel.</span>
        </div>
      )}

      <ChatComposer
        isWaiting={isWaiting}
        isDisabled={!hasSession}
        onSend={onSend}
        onStop={onStop}
      />
    </main>
  );
}
