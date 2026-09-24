"""FastAPI skeleton - the future HTTP layer described in the project plan.

Deliberately not fully implemented: the point right now is to show *where*
FastAPI sits (a thin layer over the same Agent/VectorStore that cli.py
uses) and confirm config still comes from `settings` - not to build out
file upload handling, multi-document support, auth, error handling, etc.

Run with:
    cd src
    uvicorn api:app --reload
"""

import logging
import time

from fastapi import FastAPI
from fastapi import Request
from pydantic import BaseModel

from agent import Agent
from config import settings
from embeddings.ollama_embeddings import OllamaEmbeddingClient
from llm.ollama_client import OllamaChatClient
from logging_config import configure_logging
from tools import SEARCH_DOCUMENT_TOOL, make_search_document_tool
from vector_store import VectorStore

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Local Document AI Agent")

# Composition root for the API process: one shared vector store + agent for
# the life of the process. Fine for a single-document POC; a real
# multi-user version would scope these per session/document instead of
# using module-level globals.
_vector_store = VectorStore()
_embedding_client = OllamaEmbeddingClient()
_agent = Agent(
    llm_client=OllamaChatClient(),
    tools_schema=[SEARCH_DOCUMENT_TOOL],
    tool_functions={
        "search_document": make_search_document_tool(_vector_store, _embedding_client)
    },
)
logger.info(
    "API initialized chat_model=%s embedding_model=%s collection=%s",
    settings.ollama_chat_model,
    settings.ollama_embed_model,
    settings.chroma_collection,
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Request failed method=%s path=%s", request.method, request.url.path
        )
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "Request completed method=%s path=%s status=%d duration_ms=%.1f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/health")
def health() -> dict:
    """Confirms the API is up and which models/host it's configured for."""
    return {
        "status": "ok",
        "chat_model": settings.ollama_chat_model,
        "embedding_model": settings.ollama_embed_model,
    }


@app.post("/documents")
def upload_document() -> dict:
    """TODO: accept an uploaded PDF, save it, and call ingest_pdf() on it.

    Not implemented yet - see ingestion.py, which cli.py already uses for
    exactly this. This endpoint just needs to receive the file and call it.
    """
    raise NotImplementedError("Document upload isn't wired up yet - see ingestion.py")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Ask the agent a question about whatever's currently ingested."""
    logger.info("Processing chat request message_chars=%d", len(request.message))
    answer = _agent.ask(request.message)
    logger.info("Chat request completed answer_chars=%d", len(answer))
    return ChatResponse(answer=answer)
