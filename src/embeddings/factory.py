"""Create the configured embedding provider."""

from embeddings.base import EmbeddingProvider
from embeddings.client import EmbeddingClient


def create_embedding_client() -> EmbeddingProvider:
    """Return the embedding client selected by application configuration."""
    from config import settings

    if settings.embedding_provider == "ollama":
        return EmbeddingClient(
            embedding_service_url=settings.embedding_service_url,
            embedding_model_name=settings.embedding_model_name,
        )

    raise ValueError(
        f"Unsupported embedding provider: {settings.embedding_provider}. "
        "Add its adapter to embeddings/factory.py."
    )
