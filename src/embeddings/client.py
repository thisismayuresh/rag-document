"""Generic HTTP client for the configured embedding service."""

import logging
import time

import requests

from config import settings
from embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class EmbeddingClient(EmbeddingProvider):
    """Create embeddings through the service configured by the environment."""

    def __init__(
        self,
        embedding_service_url: str | None = None,
        embedding_model_name: str | None = None,
    ) -> None:
        self.embedding_service_url = (
            embedding_service_url or settings.embedding_service_url
        )
        self.embedding_model_name = (
            embedding_model_name or settings.embedding_model_name
        )

    def embed(self, text: str) -> list[float]:
        """Request one embedding vector from the configured service."""
        started_at = time.perf_counter()
        logger.debug(
            "Requesting embedding model=%s text_chars=%d",
            self.embedding_model_name,
            len(text),
        )
        response = None
        try:
            response = requests.post(
                f"{self.embedding_service_url}/api/embeddings",
                json={"model": self.embedding_model_name, "prompt": text},
                timeout=(settings.request_timeout_seconds or None),
            )
            response.raise_for_status()
            embedding_vector = response.json()["embedding"]

        except Exception:
            logger.exception(
                "Embedding request failed model=%s status=%d",
                self.embedding_model_name,
                getattr(response, "status_code", 0),
            )
            raise

        logger.debug(
            "Embedding request completed model=%s dimensions=%d duration_ms=%.1f",
            self.embedding_model_name,
            len(embedding_vector),
            (time.perf_counter() - started_at) * 1000,
        )
        return embedding_vector
