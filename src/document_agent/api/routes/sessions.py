"""Session routes - create, inspect, and delete chat sessions."""

from fastapi import APIRouter, Depends, Response

from document_agent.api.deps import get_registry
from document_agent.api.schemas import SessionCreatedModel, SessionModel, session_to_model
from document_agent.config import settings
from document_agent.sessions import SessionRegistry

router = APIRouter()


@router.post("/sessions", response_model=SessionCreatedModel, status_code=201)
def create_session(
    registry: SessionRegistry = Depends(get_registry),
) -> SessionCreatedModel:
    """Start a new session with an empty document collection."""
    session = registry.create()
    return SessionCreatedModel(
        session_id=session.id,
        created_at=session.created_at.isoformat(),
        max_documents=settings.max_documents_per_session,
    )


@router.get("/sessions/{session_id}", response_model=SessionModel)
def get_session(
    session_id: str, registry: SessionRegistry = Depends(get_registry)
) -> SessionModel:
    """Return the session with its current document list."""
    session = registry.get(session_id)
    return session_to_model(session)


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: str, registry: SessionRegistry = Depends(get_registry)
) -> Response:
    """Delete the session and every vector it stored."""
    registry.delete(session_id)
    return Response(status_code=204)
