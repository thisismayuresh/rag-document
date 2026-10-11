import type { ChatMessage } from "../hooks/useChat";
import { ChatComposer } from "./ChatComposer";
import { ErrorBanner } from "./ErrorBanner";
import { MessageList } from "./MessageList";
import { Spinner } from "./Spinner";
import { WaitingStatus } from "./WaitingStatus";

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
          <Spinner size={20} label="Waiting for response" />
          <WaitingStatus />
          <button type="button" className="ghost-button" onClick={onStop}>
            Stop
          </button>
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
