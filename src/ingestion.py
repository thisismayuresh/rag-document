"""Turns a PDF file into searchable chunks stored in the vector store.

Kept separate from cli.py/api.py so both entry points reuse the exact
same ingestion logic instead of two slightly-different copies of it.
"""

import logging
import os

from chunker import chunk_pages
from document_loader import load_pdf
from embeddings.base import EmbeddingClient
from vector_store import VectorStore

logger = logging.getLogger(__name__)


def ingest_pdf(
    pdf_path: str, vector_store: VectorStore, embedding_client: EmbeddingClient
) -> int:
    """Load, chunk, embed, and store a PDF. Returns the number of chunks stored."""
    document_name = os.path.basename(pdf_path)

    logger.info("Loading %s", document_name)
    pages = load_pdf(pdf_path)

    logger.info("Extracted %d pages, splitting into chunks", len(pages))
    chunks = chunk_pages(pages, document_name)

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
    logger.info("Ingestion completed document=%s chunks=%d", document_name, len(chunks))

    return len(chunks)
