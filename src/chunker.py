"""Split extracted page text into overlapping chunks.

Overlap exists so a sentence that lands right on a chunk boundary doesn't
get cut in half and lose its meaning in both halves.
"""

import logging

from config import settings
from data_models import DocumentChunk, PageText

logger = logging.getLogger(__name__)


def chunk_pages(
    pages: list[PageText],
    document_name: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[DocumentChunk]:
    chunk_size = settings.chunk_size if chunk_size is None else chunk_size
    overlap = settings.chunk_overlap if overlap is None else overlap
    _validate_chunk_settings(chunk_size, overlap)

    chunks: list[DocumentChunk] = []
    next_chunk_number = 0

    for page in pages:
        for piece in _split_into_pieces(page.text, chunk_size, overlap):
            chunks.append(
                DocumentChunk(
                    chunk_id=f"chunk_{next_chunk_number}",
                    text=piece,
                    page_number=page.page_number,
                    document_name=document_name,
                )
            )
            next_chunk_number += 1

    logger.info(
        "Chunking completed document=%s pages=%d chunks=%d chunk_size=%d overlap=%d",
        document_name,
        len(pages),
        len(chunks),
        chunk_size,
        overlap,
    )
    return chunks


def _split_into_pieces(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Slide a fixed-size window over `text`, stepping by (chunk_size - overlap)."""
    step = chunk_size - overlap
    pieces: list[str] = []

    start = 0
    while start < len(text):
        piece = text[start : start + chunk_size].strip()
        if piece:
            pieces.append(piece)

        reached_end = start + chunk_size >= len(text)
        if reached_end:
            break
        start += step

    return pieces


def _validate_chunk_settings(chunk_size: int, overlap: int) -> None:
    """Reject settings that would create invalid or non-progressing windows."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
