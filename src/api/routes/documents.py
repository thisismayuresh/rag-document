"""Document routes - streaming PDF upload, listing, and removal.

Uploads are streamed to a temporary file in 64 KB chunks and rejected the
moment they exceed the configured limit, so a huge request never has to
fit in memory before being refused. Ingestion (extract -> chunk -> embed ->
store) runs in the threadpool like the rest of the blocking work.
"""

import logging
import os
import shutil
import tempfile

import requests
from fastapi import APIRouter, Depends, File, Form, UploadFile
from starlette.concurrency import run_in_threadpool

from api.deps import get_registry
from api.errors import ApiError
from api.schemas import (
    DocumentModel,
    DocumentUploadedModel,
    document_to_model,
    session_to_model,
)
from config import settings
from data_models import DocumentInfo
from ingestion import IngestionResult, ingest_pdf
from sessions import SessionRegistry, SessionState

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_CHUNK_BYTES = 64 * 1024
PDF_MAGIC = b"%PDF"


@router.post("/documents", response_model=DocumentUploadedModel, status_code=201)
async def upload_document(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    registry: SessionRegistry = Depends(get_registry),
) -> DocumentUploadedModel:
    """Stream a PDF upload to disk, ingest it, and add it to the session."""
    session = registry.get(session_id)
    document_name = _clean_filename(file.filename)
    _reject_before_storing(session, document_name)

    temp_path = await _stream_to_temp_file(file)
    try:
        result = await _ingest_upload(session, document_name, temp_path)
        size_bytes = os.path.getsize(temp_path)
        _archive_upload(session.id, document_name, temp_path)
    except ApiError:
        raise
    except requests.RequestException as exc:
        logger.exception("Embedding service failed during ingestion")
        _cleanup_partial_ingest(session, document_name)
        raise ApiError(
            502,
            "embedding_service_unavailable",
            "The embedding service did not respond while indexing the PDF.",
        ) from exc
    except Exception as exc:  # noqa: BLE001 - PDF parsing and indexing failures
        logger.exception("Ingestion failed name=%s", document_name)
        _cleanup_partial_ingest(session, document_name)
        raise ApiError(
            422,
            "ingestion_failed",
            f"Could not read or index '{document_name}': {exc}",
        ) from exc
    finally:
        _remove_if_exists(temp_path)

    document = _document_from_result(result, size_bytes)
    registry.add_document(session, document)

    return DocumentUploadedModel(
        document=document_to_model(document),
        session=session_to_model(session),
    )


@router.get("/sessions/{session_id}/documents", response_model=list[DocumentModel])
def list_documents(
    session_id: str, registry: SessionRegistry = Depends(get_registry)
) -> list[DocumentModel]:
    """Return the documents currently attached to the session."""
    session = registry.get(session_id)
    return [document_to_model(document) for document in session.documents]


@router.delete("/sessions/{session_id}/documents/{document_name}", status_code=204)
def remove_document(
    session_id: str,
    document_name: str,
    registry: SessionRegistry = Depends(get_registry),
) -> None:
    """Remove a document from the session and delete its vectors."""
    session = registry.get(session_id)
    registry.remove_document(session, document_name)

    stored_path = os.path.join(_session_dir(session.id), document_name)
    _remove_if_exists(stored_path)


def _reject_before_storing(session: SessionState, document_name: str) -> None:
    if not document_name:
        raise ApiError(400, "invalid_filename", "The upload is missing a filename.")

    if session.find_document(document_name) is not None:
        raise ApiError(
            409,
            "document_already_exists",
            f"'{document_name}' is already in this session. Remove it first "
            "if you want to upload a new version.",
        )

    if len(session.documents) >= settings.max_documents_per_session:
        raise ApiError(
            409,
            "session_limit_reached",
            f"A session can hold at most {settings.max_documents_per_session} "
            "documents. Remove one before uploading another.",
        )


async def _stream_to_temp_file(file: UploadFile) -> str:
    """Copy the upload to a temp file, enforcing the size limit as we go."""
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_path = temp.name
    total_bytes = 0
    try:
        while True:
            chunk = await file.read(UPLOAD_CHUNK_BYTES)
            if not chunk:
                break

            total_bytes += len(chunk)
            if total_bytes > settings.max_upload_bytes:
                raise ApiError(
                    413,
                    "document_too_large",
                    f"PDFs must be {settings.max_upload_mb} MB or smaller.",
                )
            temp.write(chunk)

        if total_bytes == 0:
            raise ApiError(400, "empty_file", "The uploaded file is empty.")

        _require_pdf_magic(temp_path)
        return temp_path
    except Exception:
        # Rejected uploads must not leave temp files behind.
        _remove_if_exists(temp_path)
        raise
    finally:
        temp.close()


def _require_pdf_magic(path: str) -> None:
    with open(path, "rb") as handle:
        header = handle.read(len(PDF_MAGIC))
    if header != PDF_MAGIC:
        raise ApiError(415, "unsupported_file_type", "Only PDF files can be uploaded.")


async def _ingest_upload(
    session: SessionState, document_name: str, temp_path: str
) -> IngestionResult:
    return await run_in_threadpool(
        ingest_pdf,
        temp_path,
        session.vector_store,
        session.embedding_client,
        document_name,
    )


def _cleanup_partial_ingest(session: SessionState, document_name: str) -> None:
    """Best-effort removal of any chunks a failed ingestion may have stored."""
    try:
        session.vector_store.delete_document(document_name)
    except Exception:  # noqa: BLE001 - cleanup must never mask the original error
        logger.warning("Could not clean up partial ingestion name=%s", document_name)


def _archive_upload(session_id: str, document_name: str, temp_path: str) -> None:
    """Keep the uploaded PDF under documents/<session_id>/ for reference."""
    session_dir = _session_dir(session_id)
    os.makedirs(session_dir, exist_ok=True)
    shutil.move(temp_path, os.path.join(session_dir, document_name))


def _document_from_result(
    result: IngestionResult, size_bytes: int
) -> DocumentInfo:
    return DocumentInfo(
        name=result.document_name,
        chunk_count=result.chunk_count,
        page_count=result.page_count,
        size_bytes=size_bytes,
    )


def _session_dir(session_id: str) -> str:
    return os.path.join(settings.documents_dir, session_id)


def _clean_filename(raw_filename: str | None) -> str:
    if not raw_filename:
        return ""
    return os.path.basename(raw_filename.strip())


def _remove_if_exists(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
