"""Tools available to the question-answering agent.

Retrieval only - the tools never generate answers themselves. The LLM
reasons over whatever text these return and decides what to say.

Two tools keep the model grounded in what the session actually contains:
- ``list_documents`` tells it which documents exist (so it never guesses).
- ``search_document`` retrieves chunks with document names and page numbers.
"""

import logging
import re
from typing import Callable

from document_agent.data_models import Citation, SearchResult
from document_agent.embeddings.base import EmbeddingProvider
from document_agent.vector_store import VectorStore

logger = logging.getLogger(__name__)

SEARCH_TOOL_NAME = "search_document"
LIST_TOOL_NAME = "list_documents"

SEARCH_DOCUMENT_SCHEMA: dict = {
    "type": "function",
    "function": {
        "name": "search_document",
        "description": (
            "Search the user's uploaded documents for chunks relevant to a "
            "query. Results include the document name and page number. Use "
            "this whenever you need document content to answer the user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The search query, phrased as the information you "
                        "need to find."
                    ),
                }
            },
            "required": ["query"],
        },
    },
}

LIST_DOCUMENTS_SCHEMA: dict = {
    "type": "function",
    "function": {
        "name": "list_documents",
        "description": (
            "List the documents available in this session. Call this first "
            "when you need to know which documents exist before searching."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}


class Tools:
    """Application tools available to the document question-answering agent."""

    SEARCH_TOOL_NAME = SEARCH_TOOL_NAME
    LIST_TOOL_NAME = LIST_TOOL_NAME

    def __init__(
        self, vector_store: VectorStore, embedding_client: EmbeddingProvider
    ) -> None:
        self._vector_store = vector_store
        self._embedding_client = embedding_client

    def schemas(self) -> list[dict]:
        """Tool schemas in the shape the chat API expects."""
        return [SEARCH_DOCUMENT_SCHEMA, LIST_DOCUMENTS_SCHEMA]

    def registry(self) -> dict[str, Callable[..., str]]:
        """Map tool names to the callables the agent should invoke."""
        return {
            self.SEARCH_TOOL_NAME: self.search_document,
            self.LIST_TOOL_NAME: self.list_documents,
        }

    def search_document(self, query: str) -> str:
        """Search the documents for chunks relevant to ``query``."""
        logger.info("Searching documents query_chars=%d", len(query))
        query_embedding = self._embedding_client.embed(query)
        results = self._vector_store.query(query_embedding)

        if not results:
            logger.info("Document search returned no results")
            return (
                "No relevant information found in the uploaded documents "
                "for that query."
            )

        logger.info("Document search returned results=%d", len(results))
        return "\n\n".join(_format_result(result) for result in results)

    def list_documents(self) -> str:
        """Describe the documents currently stored for this session."""
        summaries = self._vector_store.list_documents()
        if not summaries:
            return (
                "No documents are available in this session. Ask the user "
                "to upload a PDF first."
            )

        lines = [f"- {summary.name} ({summary.chunk_count} chunks)" for summary in summaries]
        return "Available documents:\n" + "\n".join(lines)


def _format_result(result: SearchResult) -> str:
    score = (
        f"{result.relevance_score:.2f}" if result.relevance_score is not None else "n/a"
    )
    header = (
        f"[Document: {result.document_name} | Page: {result.page_number} "
        f"| Score: {score}]"
    )
    return f"{header}\n{result.text}"


# Matches the header `_format_result` writes. The agent uses this to pull
# the (document, page) pairs back out of a search result so the API can
# return them as structured citations. Keep the two functions in sync.
_RESULT_HEADER = re.compile(
    r"\[Document: (.+?) \| Page: (\d+) \| Score: [^\]]*\]"
)


def parse_citations(search_result_text: str) -> list[Citation]:
    """Extract the cited (document, page) pairs from a search result string."""
    return [
        Citation(document_name=name, page_number=int(page))
        for name, page in _RESULT_HEADER.findall(search_result_text)
    ]
