// Cycling status line shown while the model is thinking. A new phrase
// slides up into place every few seconds; plain state + CSS keyframes,
// no animation library.

import { useEffect, useState } from "react";

export interface WaitingStatusProps {
  /** Milliseconds each phrase stays on screen before the next one. */
  intervalMs?: number;
}

const PHRASES = [
  "Waiting for the model...",
  "Searching your documents...",
  "Reading the relevant pages...",
  "Still working - the model can take a while.",
  "Almost there...",
];

export function WaitingStatus({ intervalMs = 4000 }: WaitingStatusProps) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % PHRASES.length);
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [intervalMs]);

  return (
    <span className="waiting-status">
      {/* Re-mounting on key restarts the slide-up animation each time. */}
      <span key={index} className="waiting-status-text">
        {PHRASES[index]}
      </span>
    </span>
  );
}
