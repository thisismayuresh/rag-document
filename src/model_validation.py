"""Fail-fast startup checks for the configured models and vector store.

The user can point the app at any Ollama chat model and any Ollama embedding
model. That freedom means a typo or a swapped name (a chat model in
EMBEDDING_MODEL_NAME, for example) is easy to hit, so the API validates the
configuration on startup and refuses to boot with a confusing runtime error
later. Each check appends a human-readable message; all messages are raised
together so one restart shows every problem at once.
"""

import logging

import chromadb
import requests

from config import settings

logger = logging.getLogger(__name__)

PROBE_TEXT = "startup validation probe"
SHORT_TIMEOUT_SECONDS = 10


class StartupConfigurationError(RuntimeError):
    """Raised when startup validation fails. The message lists every problem."""


def validate_startup_configuration() -> None:
    """Raise StartupConfigurationError if models or ChromaDB are unusable."""
    problems: list[str] = []
    problems.extend(_check_chat_configuration())
    problems.extend(_check_embedding_configuration())
    problems.extend(_check_vector_store())

    if not problems:
        logger.info("Startup validation passed")
        return

    detail = "\n".join(f"  - {problem}" for problem in problems)
    raise StartupConfigurationError(
        f"Startup validation failed:\n{detail}\n"
        "Fix the values in .env (see .env.example) and restart."
    )


def _check_chat_configuration() -> list[str]:
    if settings.chat_provider != "ollama":
        return []

    available = _ollama_model_names(settings.chat_service_url)
    if available is None:
        return [
            f"Cannot reach the chat service at {settings.chat_service_url} "
            "(CHAT_SERVICE_URL). Is Ollama running?"
        ]

    if _model_available(settings.chat_model_name, available):
        return []

    return [
        f"Chat model '{settings.chat_model_name}' (CHAT_MODEL_NAME) is not "
        f"available on {settings.chat_service_url}. "
        f"Available models: {_format_model_list(available)}"
    ]


def _check_embedding_configuration() -> list[str]:
    if settings.embedding_provider != "ollama":
        return []

    available = _ollama_model_names(settings.embedding_service_url)
    if available is None:
        return [
            f"Cannot reach the embedding service at "
            f"{settings.embedding_service_url} (EMBEDDING_SERVICE_URL). "
            "Is Ollama running?"
        ]

    if not _model_available(settings.embedding_model_name, available):
        return [
            f"Embedding model '{settings.embedding_model_name}' "
            f"(EMBEDDING_MODEL_NAME) is not available on "
            f"{settings.embedding_service_url}. "
            f"Available models: {_format_model_list(available)}"
        ]

    # A model can be listed and still refuse to embed (a chat model with the
    # wrong name pasted into EMBEDDING_MODEL_NAME). One tiny live call catches
    # that class of mistake before any user request hits it.
    return _probe_embedding_model()


def _probe_embedding_model() -> list[str]:
    try:
        response = requests.post(
            f"{settings.embedding_service_url}/api/embeddings",
            json={"model": settings.embedding_model_name, "prompt": PROBE_TEXT},
            timeout=SHORT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return [
            f"Embedding model '{settings.embedding_model_name}' "
            "(EMBEDDING_MODEL_NAME) failed a test embedding call: "
            f"{exc}. The model may not be an embedding model - check that "
            "EMBEDDING_MODEL_NAME names an embedding model such as "
            "nomic-embed-text, not a chat model."
        ]

    embedding = response.json().get("embedding")
    if not embedding:
        return [
            f"Embedding model '{settings.embedding_model_name}' returned an "
            "empty embedding for a test input. It does not look usable."
        ]
    return []


def _check_vector_store() -> list[str]:
    try:
        client = chromadb.HttpClient(
            host=settings.chroma_host, port=settings.chroma_port
        )
        client.list_collections()
    except Exception as exc:  # noqa: BLE001 - chroma raises library-specific errors
        return [
            f"Cannot reach ChromaDB at {settings.chroma_host}:"
            f"{settings.chroma_port} (CHROMA_HOST/CHROMA_PORT): {exc}"
        ]
    return []


def _ollama_model_names(service_url: str) -> list[str] | None:
    """Return the model names listed by an Ollama server, or None if unreachable."""
    try:
        response = requests.get(
            f"{service_url}/api/tags", timeout=SHORT_TIMEOUT_SECONDS
        )
        response.raise_for_status()
    except requests.RequestException:
        return None

    models = response.json().get("models", [])
    return [model["name"] for model in models if "name" in model]


def _model_available(configured_name: str, available: list[str]) -> bool:
    if configured_name in available:
        return True
    # Ollama reports untagged models as "name:latest"; accept the untagged form.
    return f"{configured_name}:latest" in available


def _format_model_list(available: list[str]) -> str:
    if not available:
        return "none (run 'ollama pull <model>' first)"
    return ", ".join(sorted(available))
