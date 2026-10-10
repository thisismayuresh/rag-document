"""Wrapper around a ChromaDB server (see docker-compose.yml).

Everything the rest of the app needs from Chroma goes through this one
class. If you ever swap Chroma for another vector DB, this is the only
file that should need to change.

Each session gets its own VectorStore bound to its own collection, so
documents never leak between sessions and deleting a document (or a whole
session) removes every reference from search results.
"""

import logging

import chromadb

from config import settings
from data_models import DocumentChunk, DocumentSummary, SearchResult

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, collection_name: str | None = None) -> None:
        self._collection_name = collection_name or settings.chroma_collection
        logger.info(
            "Connecting to vector store host=%s port=%d collection=%s",
            settings.chroma_host,
            settings.chroma_port,
            self._collection_name,
        )
        self._client = chromadb.HttpClient(
            host=settings.chroma_host, port=settings.chroma_port
        )
        self._collection = self._client.get_or_create_collection(
            self._collection_name
        )

    @property
    def collection_name(self) -> str:
        return self._collection_name

    def add_chunks(
        self, chunks: list[DocumentChunk], embeddings: list[list[float]]
    ) -> None:
        logger.info("Adding chunks to vector store count=%d", len(chunks))
        self._collection.add(
            ids=[f"{chunk.document_name}::{chunk.chunk_id}" for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {"page": chunk.page_number, "document": chunk.document_name}
                for chunk in chunks
            ],
        )

    def query(
        self, query_embedding: list[float], top_k: int | None = None
    ) -> list[SearchResult]:
        top_k = top_k or settings.top_k_results
        logger.debug("Querying vector store top_k=%d", top_k)
        results = self._collection.query(
            query_embeddings=[query_embedding], n_results=top_k
        )

        texts = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        search_results = [
            SearchResult(
                text=text,
                page_number=metadata.get("page"),
                document_name=metadata.get("document"),
                relevance_score=(1 - distance) if distance is not None else None,
            )
            for text, metadata, distance in zip(texts, metadatas, distances)
        ]
        logger.info(
            "Vector search completed requested=%d returned=%d",
            top_k,
            len(search_results),
        )
        return search_results

    def list_documents(self) -> list[DocumentSummary]:
        """Summarize the documents stored in this collection."""
        stored = self._collection.get(include=["metadatas"])
        counts: dict[str, int] = {}
        for metadata in stored.get("metadatas", []):
            name = (metadata or {}).get("document")
            if name:
                counts[name] = counts.get(name, 0) + 1

        summaries = [
            DocumentSummary(name=name, chunk_count=count)
            for name, count in sorted(counts.items())
        ]
        logger.info("Listed stored documents count=%d", len(summaries))
        return summaries

    def delete_document(self, document_name: str) -> None:
        """Remove every chunk belonging to one document."""
        logger.info("Deleting document from vector store name=%s", document_name)
        self._collection.delete(where={"document": document_name})

    def drop_collection(self) -> None:
        """Delete the collection itself. Used when a session is removed."""
        logger.info("Dropping vector store collection=%s", self._collection_name)
        self._client.delete_collection(self._collection_name)

    def is_empty(self) -> bool:
        count = self._collection.count()
        logger.info("Vector store contains chunks=%d", count)
        return count == 0
