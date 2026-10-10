"""Pydantic models for the HTTP API - the request/response contract."""

from pydantic import BaseModel

from config import settings
from data_models import DocumentInfo
from sessions import SessionState


class DocumentModel(BaseModel):
    name: str
    chunk_count: int
    page_count: int
    size_bytes: int


class SessionModel(BaseModel):
    session_id: str
    created_at: str
    max_documents: int
    documents: list[DocumentModel]


class SessionCreatedModel(BaseModel):
    session_id: str
    created_at: str
    max_documents: int


class DocumentUploadedModel(BaseModel):
    document: DocumentModel
    session: SessionModel


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str


class HealthResponse(BaseModel):
    status: str
    chat_provider: str
    chat_model: str
    embedding_provider: str
    embedding_model: str
    max_documents_per_session: int
    max_upload_mb: int


def document_to_model(document: DocumentInfo) -> DocumentModel:
    return DocumentModel(
        name=document.name,
        chunk_count=document.chunk_count,
        page_count=document.page_count,
        size_bytes=document.size_bytes,
    )


def session_to_model(session: SessionState) -> SessionModel:
    return SessionModel(
        session_id=session.id,
        created_at=session.created_at.isoformat(),
        max_documents=settings.max_documents_per_session,
        documents=[document_to_model(document) for document in session.documents],
    )
