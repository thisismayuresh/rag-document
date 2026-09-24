"""Typed data structures shared across the pipeline.

Plain dicts work, but `chunk["txt"]` (typo for "text") fails silently at
runtime and tells you nothing when you read the code. Dataclasses make the
shape of the data obvious at a glance and let your editor/type-checker
catch mistakes before you run anything.
"""

from dataclasses import dataclass


@dataclass
class PageText:
    """One page of extracted PDF text."""

    page_number: int
    text: str


@dataclass
class DocumentChunk:
    """A chunk of a document, ready to be embedded and stored."""

    chunk_id: str
    text: str
    page_number: int
    document_name: str


@dataclass
class SearchResult:
    """A single hit returned from the vector store."""

    text: str
    page_number: int
    document_name: str
    relevance_score: float | None
