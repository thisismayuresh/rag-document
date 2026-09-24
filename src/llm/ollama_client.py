"""ChatClient implementation backed by a local Ollama server.

To use a different model later, either:
  - pass a different `model=` to OllamaChatClient (still Ollama), or
  - write a new class implementing ChatClient (e.g. OpenAIChatClient) and
    hand that to Agent instead - nothing else in the codebase changes.
"""

import logging
import time
from typing import Any

import requests

from config import settings
from llm.base import ChatClient

logger = logging.getLogger(__name__)


class OllamaChatClient(ChatClient):
    """Chat adapter for an Ollama-compatible chat service."""

    def __init__(
        self,
        chat_service_url: str | None = None,
        chat_model_name: str | None = None,
    ) -> None:
        self.chat_service_url = chat_service_url or settings.chat_service_url
        self.chat_model_name = chat_model_name or settings.chat_model_name

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        logger.debug(
            "Requesting chat model=%s messages=%d tools=%d",
            self.chat_model_name,
            len(messages),
            len(tools or []),
        )
        response = None
        try:
            response = requests.post(
                f"{self.chat_service_url}/api/chat",
                json={
                    "model": self.chat_model_name,
                    "messages": messages,
                    "tools": tools or [],
                    "stream": False,
                },
                timeout=(settings.request_timeout_seconds or None),
            )
            response.raise_for_status()
            message = response.json()["message"]
        except Exception:
            logger.exception(
                "Chat request failed model=%s status=%d",
                self.chat_model_name,
                getattr(response, "status_code", 0),
            )
            raise
        logger.debug(
            "Chat request completed model=%s tool_calls=%d duration_ms=%.1f",
            self.chat_model_name,
            len(message.get("tool_calls", [])),
            (time.perf_counter() - started_at) * 1000,
        )
        return message
