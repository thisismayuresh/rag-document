"""FastAPI entry point for the local document agent.

Composition root: wires configuration validation, the session registry,
CORS, logging, and the route modules. Nothing here talks to Ollama or
ChromaDB directly - that lives behind sessions, tools, and the clients.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.errors import register_exception_handlers
from api.routes import chat, documents, health, sessions
from config import settings
from embeddings.factory import create_embedding_client
from llm.factory import create_chat_client
from logging_config import configure_logging
from model_validation import validate_startup_configuration
from sessions import SessionRegistry

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate configuration, then hand a live registry to the routes."""
    validate_startup_configuration()

    registry = SessionRegistry(
        embedding_client=create_embedding_client(),
        chat_client=create_chat_client(),
    )
    app.state.sessions = registry

    logger.info(
        "API ready chat_provider=%s chat_model=%s embedding_provider=%s "
        "embedding_model=%s max_documents=%d max_upload_mb=%d",
        settings.chat_provider,
        settings.chat_model_name,
        settings.embedding_provider,
        settings.embedding_model_name,
        settings.max_documents_per_session,
        settings.max_upload_mb,
    )
    yield


app = FastAPI(title="Local Document AI Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origin_list(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


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


app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(documents.router)
app.include_router(chat.router)
