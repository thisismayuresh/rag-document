"""Every embedding backend implements this interface (mirrors llm/base.py).

Same reasoning as ChatClient: the rest of the app (tools.py, ingestion.py)
depends on `EmbeddingClient`, never on Ollama directly.
"""

from abc import ABC, abstractmethod


class EmbeddingClient(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError
