"""Interface implemented by every embedding backend.

The rest of the application depends on `EmbeddingProvider`, never on a
specific embedding service or model.
"""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError
