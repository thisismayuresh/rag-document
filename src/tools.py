"""The agent's first tool: search_document.

Retrieval only - it must NOT generate answers itself. The LLM is what
reasons over whatever text this returns and decides what to say.
"""

import logging

from data_models import SearchResult
from embeddings.base import EmbeddingClient
from vector_store import VectorStore

logger = logging.getLogger(__name__)

SEARCH_DOCUMENT_SCHEMA: dict = {
    "type": "function",
    "function": {
        "name": "search_document",
        "description": (
            "Search the ingested document for chunks relevant to a query. "
            "Use this whenever you need information from the document to "
            "answer the user's question."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query, phrased as the information you need to find.",
                }
            },
            "required": ["query"],
        },
    },
}


class Tools:
    """Application tools available to the document question-answering agent."""

    name = "search_document"
    schema = SEARCH_DOCUMENT_SCHEMA

    def __init__(
        self, vector_store: VectorStore, embedding_client: EmbeddingClient
    ) -> None:
        self._vector_store = vector_store
        self._embedding_client = embedding_client

    def search_document(self, query: str) -> str:
        """Search the document for chunks relevant to ``query``."""
        logger.info("Searching document query_chars=%d", len(query))
        query_embedding = self._embedding_client.embed(query)
        results = self._vector_store.query(query_embedding)

        if not results:
            logger.info("Document search returned no results")
            return "No relevant information found in the document."

        logger.info("Document search returned results=%d", len(results))
        return "\n\n".join(_format_result(result) for result in results)

    def __call__(self, query: str) -> str:
        """Allow this tool to be registered directly with the agent."""
        return self.search_document(query)


def _format_result(result: SearchResult) -> str:
    score = (
        f"{result.relevance_score:.2f}" if result.relevance_score is not None else "n/a"
    )
    header = (
        f"[Document: {result.document_name} | Page: {result.page_number} "
        f"| Score: {score}]"
    )
    return f"{header}\n{result.text}"
