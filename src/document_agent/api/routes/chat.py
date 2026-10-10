"""Chat routes - ask a question about a session's documents.

The endpoint is intentionally synchronous with no server-side timeout: the
LLM may take minutes, and the client decides when to give up by aborting
the request. Each session owns its own conversation, so history never
bleeds between sessions.
"""

import requests
from fastapi import APIRouter, Depends

from document_agent.api.deps import get_registry
from document_agent.api.errors import ApiError
from document_agent.api.schemas import ChatRequest, ChatResponse
from document_agent.sessions import SessionRegistry

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest, registry: SessionRegistry = Depends(get_registry)
) -> ChatResponse:
    """Answer a question using the session's documents and conversation."""
    session = registry.get(payload.session_id)

    try:
        answer = session.agent.ask(payload.message)
    except requests.RequestException as exc:
        raise ApiError(
            502,
            "chat_service_unavailable",
            "The chat model did not respond. Check that Ollama is running "
            "and the model is available, then try again.",
        ) from exc

    return ChatResponse(answer=answer)
