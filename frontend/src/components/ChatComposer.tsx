import { useState } from "react";
import type { KeyboardEvent } from "react";

interface ChatComposerProps {
  isWaiting: boolean;
  isDisabled: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
}

export function ChatComposer({ isWaiting, isDisabled, onSend, onStop }: ChatComposerProps) {
  const [draft, setDraft] = useState("");

  function handleSubmit(): void {
    const text = draft.trim();
    if (!text || isWaiting || isDisabled) {
      return;
    }
    setDraft("");
    onSend(text);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>): void {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="chat-composer">
      <textarea
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question about your documents..."
        disabled={isDisabled}
        aria-label="Chat message"
      />
      {isWaiting ? (
        <button type="button" className="stop-button" onClick={onStop}>
          Stop
        </button>
      ) : (
        <button
          type="button"
          className="send-button"
          onClick={handleSubmit}
          disabled={isDisabled || draft.trim() === ""}
        >
          Send
        </button>
      )}
    </div>
  );
}
