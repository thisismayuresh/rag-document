"""The agent's first tool: search_document.

Retrieval only - it must NOT generate answers itself. The LLM is what
reasons over whatever text this returns and decides what to say.
"""

import logging
from typing import Callable

from embeddings.base import EmbeddingClient
from models import SearchResult
from vector_store import VectorStore

logger = logging.getLogger(__name__)

SEARCH_DOCUMENT_TOOL: dict = {
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


def make_search_document_tool(
    vector_store: VectorStore, embedding_client: EmbeddingClient
) -> Callable[[str], str]:
    """Build the `search_document` function, bound to a specific store/embedder.

    Returned as a closure so the agent can treat every tool the same way -
    a plain `Callable[[str], str]` - regardless of what it's built from.
    """

    def search_document(query: str) -> str:
        logger.info("Searching document query_chars=%d", len(query))
        query_embedding = embedding_client.embed(query)
        results = vector_store.query(query_embedding)

        if not results:
            logger.info("Document search returned no results")
            return "No relevant information found in the document."

        logger.info("Document search returned results=%d", len(results))
        return "\n\n".join(_format_result(result) for result in results)

    return search_document


def _format_result(result: SearchResult) -> str:
    score = (
        f"{result.relevance_score:.2f}" if result.relevance_score is not None else "n/a"
    )
    return f"[Document: {result.document_name} | Page: {result.page_number} | Score: {score}]\n{result.text}"
