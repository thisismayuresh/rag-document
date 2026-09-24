"""EmbeddingClient implementation backed by a local Ollama server."""

import logging
import time

import requests

from config import settings
from embeddings.base import EmbeddingClient

logger = logging.getLogger(__name__)


class OllamaEmbeddingClient(EmbeddingClient):
    def __init__(self, host: str | None = None, model: str | None = None) -> None:
        self.host = host or settings.ollama_host
        self.model = model or settings.ollama_embed_model

    def embed(self, text: str) -> list[float]:
        started_at = time.perf_counter()
        logger.debug(
            "Requesting embedding model=%s text_chars=%d", self.model, len(text)
        )
        response = None
        try:
            response = requests.post(
                f"{self.host}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=(settings.request_timeout_seconds or None),
            )
            response.raise_for_status()
            embedding = response.json()["embedding"]
        except Exception:
            logger.exception(
                "Embedding request failed model=%s status=%d",
                self.model,
                getattr(response, "status_code", 0),
            )
            raise
        logger.debug(
            "Embedding request completed model=%s dimensions=%d duration_ms=%.1f",
            self.model,
            len(embedding),
            (time.perf_counter() - started_at) * 1000,
        )
        return embedding
