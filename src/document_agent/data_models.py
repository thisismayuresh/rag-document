"""Application data structures shared across the document pipeline."""

from dataclasses import dataclass


@dataclass
class PageText:
    """Text extracted from one PDF page."""

    page_number: int
    text: str


@dataclass
class DocumentChunk:
    """A document text chunk ready to embed and store."""

    chunk_id: str
    text: str
    page_number: int
    document_name: str


@dataclass
class SearchResult:
    """A document chunk returned by vector search."""

    text: str
    page_number: int
    document_name: str
    relevance_score: float | None


@dataclass
class DocumentSummary:
    """What the vector store knows about one stored document."""

    name: str
    chunk_count: int


@dataclass
class DocumentInfo:
    """A document uploaded to a session."""

    name: str
    chunk_count: int
    page_count: int
    size_bytes: int