"""Every chat-capable LLM backend implements this one interface.

This is what decouples the agent from Ollama specifically. `agent.py`
only ever talks to a `ChatClient` - it has no idea whether that's Ollama,
OpenAI, vLLM, or a mock used in tests. Swapping backends later means
writing one new class in this package, not touching agent.py at all.
"""

from abc import ABC, abstractmethod
from typing import Any


class ChatClient(ABC):
    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send the conversation so far to the model and return its reply.

        The returned dict follows the OpenAI/Ollama message shape:
            {"role": "assistant", "content": "...", "tool_calls": [...] | None}
        """
        raise NotImplementedError
