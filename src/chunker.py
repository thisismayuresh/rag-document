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
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

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
