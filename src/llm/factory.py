"""Create the configured chat provider."""

from llm.base import ChatClient
from llm.ollama_client import OllamaChatClient


def create_chat_client() -> ChatClient:
    """Return the chat client selected by application configuration."""
    from config import settings

    if settings.chat_provider == "ollama":
        return OllamaChatClient(
            chat_service_url=settings.chat_service_url,
            chat_model_name=settings.chat_model_name,
        )

    raise ValueError(
        f"Unsupported chat provider: {settings.chat_provider}. "
        "Add its adapter to llm/factory.py."
    )
