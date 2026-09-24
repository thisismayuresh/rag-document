"""FastAPI entry point for the local document agent."""

import logging
import time

from fastapi import FastAPI, Request
from pydantic import BaseModel

from agent import Agent
from config import settings
from embeddings.ollama_embeddings import OllamaEmbeddingClient
from llm.ollama_client import OllamaChatClient
from logging_config import configure_logging
from tools import Tools
from vector_store import VectorStore

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Local Document AI Agent")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


def build_agent() -> Agent:
    """Construct the agent and wire its infrastructure dependencies."""
    vector_store = VectorStore()
    embedding_client = OllamaEmbeddingClient()
    tools = Tools(vector_store, embedding_client)

    return Agent(
        llm_client=OllamaChatClient(),
        tools_schema=[tools.schema],
        tool_functions={tools.name: tools.search_document},
    )


_agent = build_agent()
logger.info(
    "API initialized chat_model=%s embedding_model=%s collection=%s",
    settings.ollama_chat_model,
    settings.ollama_embed_model,
    settings.chroma_collection,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log the result and duration of every HTTP request."""
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
def health() -> dict[str, str]:
    """Return service status and the configured model names."""
    return {
        "status": "ok",
        "chat_model": settings.ollama_chat_model,
        "embedding_model": settings.ollama_embed_model,
    }


@app.post("/documents")
def upload_document() -> dict[str, str]:
    """Placeholder for the future PDF upload endpoint."""
    raise NotImplementedError("Document upload is not wired up yet")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Answer a question about the currently indexed document."""
    logger.info("Processing chat request message_chars=%d", len(request.message))
    answer = _agent.ask(request.message)
    logger.info("Chat request completed answer_chars=%d", len(answer))
    return ChatResponse(answer=answer)
