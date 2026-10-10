"""Turns a PDF file into searchable chunks stored in the vector store.

Kept separate from the CLI and the API so every entry point reuses the
exact same ingestion logic instead of two slightly-different copies.
"""

import logging
import os
from dataclasses import dataclass

from chunker import chunk_pages
from document_loader import load_pdf
from embeddings.base import EmbeddingProvider
from vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionResult:
    """What a completed ingestion produced."""

    document_name: str
    page_count: int
    chunk_count: int


def ingest_pdf(
    pdf_path: str,
    vector_store: VectorStore,
    embedding_client: EmbeddingProvider,
    document_name: str | None = None,
) -> IngestionResult:
    """Load, chunk, embed, and store a PDF.

    ``document_name`` defaults to the file's basename. Callers that ingest
    from a temporary upload file pass the original filename so search
    results and the UI show what the user actually uploaded.
    """
    resolved_name = document_name or os.path.basename(pdf_path)

    logger.info("Loading %s", resolved_name)
    pages = load_pdf(pdf_path)

    logger.info("Extracted %d pages, splitting into chunks", len(pages))
    chunks = chunk_pages(pages, resolved_name)

    logger.info("Embedding %d chunks", len(chunks))
    embeddings = [embedding_client.embed(chunk.text) for chunk in chunks]
    if len(embeddings) != len(chunks):
        logger.error(
            "Embedding count mismatch chunks=%d embeddings=%d",
            len(chunks),
            len(embeddings),
        )
        raise RuntimeError("Embedding count does not match chunk count")

    logger.info("Storing chunks in the vector store")
    vector_store.add_chunks(chunks, embeddings)
    logger.info(
        "Ingestion completed document=%s pages=%d chunks=%d",
        resolved_name,
        len(pages),
        len(chunks),
    )

    return IngestionResult(
        document_name=resolved_name,
        page_count=len(pages),
        chunk_count=len(chunks),
    )
