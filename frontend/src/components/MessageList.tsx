import { useEffect, useRef } from "react";

import type { ChatMessage } from "../hooks/useChat";
import { MessageCitations } from "./MessageCitations";

interface MessageListProps {
  messages: ChatMessage[];
}

export function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return null;
  }

  return (
    <div className="message-list">
      {messages.map((message) => (
        <div key={message.id} className={`message ${message.role}`}>
          <span className="message-role">
            {message.role === "user" ? "You" : "Assistant"}
          </span>
          <span className="message-content">{message.content}</span>
          {message.role === "assistant" && (
            <MessageCitations citations={message.citations} />
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
