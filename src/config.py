"""Centralized configuration, loaded once from environment variables / .env.

Every other module imports `settings` from here instead of calling
os.getenv() directly. That means one place to see every configurable
value, and one place to add a new one - no hunting through the codebase
for stray os.getenv() calls.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _int_env(key: str, default: int) -> int:
    return int(os.getenv(key, default))


@dataclass(frozen=True)
class Settings:
    # --- Ollama: used for both chat and embeddings ---
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_chat_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    ollama_embed_model: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    # --- ChromaDB ---
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = _int_env("CHROMA_PORT", 8000)
    chroma_collection: str = os.getenv("CHROMA_COLLECTION", "documents")

    # --- Chunking / retrieval ---
    chunk_size: int = _int_env("CHUNK_SIZE", 800)
    chunk_overlap: int = _int_env("CHUNK_OVERLAP", 150)
    top_k_results: int = _int_env("TOP_K_RESULTS", 4)

    # --- Networking / agent behaviour ---
    request_timeout_seconds: int = _int_env("REQUEST_TIMEOUT_SECONDS", 120)
    max_tool_rounds: int = _int_env("MAX_TOOL_ROUNDS", 4)


settings = Settings()
