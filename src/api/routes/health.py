"""GET /health - service status and configured limits."""

from fastapi import APIRouter

from api.schemas import HealthResponse
from config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service status, configured models, and upload limits."""
    return HealthResponse(
        status="ok",
        chat_provider=settings.chat_provider,
        chat_model=settings.chat_model_name,
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model_name,
        max_documents_per_session=settings.max_documents_per_session,
        max_upload_mb=settings.max_upload_mb,
    )
